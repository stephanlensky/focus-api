from bs4 import BeautifulSoup
from bs4 import Comment
from dateutil.parser import parse
from datetime import date
import sys


# returns a tuple with the current marking period and available marking periods for the page
# [0] - current mp year
# [1] - current mp id
# [2] - available years
# [3] - available ids
def __get_marking_periods__(page):
    years = page.find('select', {'name': 'side_syear'}).findChildren()
    selected_year = ''
    available_years = []
    for y in years:
        if y.has_attr('selected'):
            selected_year = int(y['value'])
        available_years.append(int(y['value']))

    mps = page.find('select', {'name': 'side_mp'}).findChildren()
    selected_mp = ''
    available_mps = []
    for mp in mps:
        if mp.has_attr('selected'):
            selected_mp = int(mp['value'])
        available_mps.append(int(mp['value']))

    return selected_year, selected_mp, available_years, available_mps

# add marking period info to a dictionary
def __add_marking_periods_to__(d, mp):
    d['current_mp_year'] = mp[0]
    d['current_mp_id'] = mp[1]
    d['available_mp_years'] = mp[2]
    d['available_mp_ids'] = mp[3]
    return d


# parse the homepage of Focus (the portal)
def parse_portal(portal):
    portal = BeautifulSoup(portal, 'html.parser')
    featured_progs = portal.find('td', text='Featured Programs').parent.parent
    links = featured_progs.find_all('a')

    courses = {}
    url_start = 'Modules.php?modname=Grades/StudentGBGrades.php?course_period_id='
    for a in links:
        if 'href' in a.attrs and a.attrs['href'].startswith(url_start):
            id = int(a.attrs['href'][len(url_start):])
            if id not in courses:
                courses[id] = {}

            t = a.text.replace(u'\xa0', u' ') # replace non-breaking space with normal space
            if t.find('%') > 0:
                courses[id]['percent_grade'] = int(t[:t.find('%')])
                courses[id]['letter_grade'] = t[t.find(' ') + 1:]
            elif t.find('Period') > 0:
                data = t.split(" - ")
                courses[id]['name'] = data[0]
                courses[id]['period'] = int(data[1][len("Period "):])
                courses[id]['days'] = data[2]
                courses[id]['teacher'] = data[4]
            else:
                continue

    # convert from a dict that has id -> course info to a list that has each course
    course_list = []
    for id in courses:
        course = {"id":id}
        course.update(courses[id])
        course_list.append(course)
    courses = course_list

    events = []
    upcoming = portal.find('td', {'class': 'portal_block_Upcoming'})
    links = upcoming.find_all('a')
    links.pop(0)
    comments = upcoming.find_all(string=lambda text: isinstance(text, Comment))
    for a, c in zip(links, comments):
        if a.text.find(':') < 0:
            continue
        event = {}
        event['description'] = a.text[a.text.find(": ") + 2:]
        year = int(c[0:5])
        month = int(c[5:7])
        day = int(c[7:9])
        event['date'] = date(year, month, day).isoformat()
        events.append(event)

    return __add_marking_periods_to__({'events': events, 'courses': courses}, __get_marking_periods__(portal))


# parse a course page
def parse_course(course):
    course = BeautifulSoup(course, 'html.parser')
    course_info = {}

    metadata = course.find('img', {'src':'modules/Grades/Grades.png'})
    if metadata:
        metadata = metadata.text
        metadata = metadata.split(" - ")
        course_info['name'] = metadata[0]
        course_info['period'] = int(metadata[1][len("Period "):])
        course_info['teacher'] = metadata[-1]

    category_table = course.find('td', {'class': 'GrayDrawHeader'})
    if category_table:
        curr_grade = course.find(id='currentStudentGrade[]').text
        curr_grade = curr_grade.replace(u'\xa0', u' ') # replace non-breaking space with normal space
        if curr_grade.find('%') > 0:
            course_info['percent_grade'] = int(curr_grade[:curr_grade.find('%')])
            course_info['letter_grade'] = curr_grade[curr_grade.find(' ') + 1:]

        categories = []
        tr = category_table.find_all('tr')
        if tr:
            names = []
            td = tr[0].find_all('td')
            td.pop()
            for e in td:
                if e.text.strip == "" or e.text == "Weighted Grade":
                    continue
                names.append(e.text)
            weights = []
            for e in tr[1].find_all('td'):
                if e.text.strip == "":
                    continue
                weights.append(e.text)
            scores = []
            td = tr[2].find_all('td')
            td.pop()
            for e in td:
                if e.text.strip == "":
                    continue
                scores.append(e.text)
            for n, w, s in zip(names, weights, scores):
                category = {
                    'name': n,
                    'percent_weight': int(w[:len(w) - 1])
                }
                s = s.split("%\xa0")
                if len(s) == 2:
                    category['percent_grade'] = int(s[0])
                    category['letter_grade'] = s[1]

                categories.append(category)

            course_info['categories'] = categories

    assignments = []
    count = 1
    tr = course.find('tr', id='LOy_row' + str(count))
    while tr:
        td = tr.find_all('td', {'class': 'LO_field'})
        assignment = {}
        name = td[0].text

        div = td[0].find('div')
        if div is not None:
            description_start = div.attrs['onmouseover'].find('","') + 3
            description_end = div.attrs['onmouseover'].find('"],["')
            description = div.attrs['onmouseover'][description_start:description_end]
            description = description.replace('\\r\\n', '\n')
            assignment['description'] = description

        grade_img = tr.find('img')
        if grade_img is not None:
            status = 'pass' if grade_img.attrs['src'] == 'assets/check.png' else 'fail'
        else:
            grade_ratio = td[1].text.split(' / ')
            assignment['max_grade'] = int(grade_ratio[1])
            if grade_ratio[0] == '*':
                status = 'excluded'
            elif grade_ratio[0] == 'NG':
                status = 'ng'
            elif grade_ratio[0] == 'M':
                status = 'missing'
            elif td[2].text == "Extra Credit":
                status = 'extra'
            else:
                status = 'graded'
                assignment['student_grade'] = float(grade_ratio[0])
                overall_grade = td[2].text.split("% ")
                assignment['percent_overall_grade'] = int(overall_grade[0])
                assignment['letter_overall_grade'] = overall_grade[1]

        if td[3].text.strip() != '':
            assignment['comment'] = td[3].text

        if td[6].text.strip() != '':
            assignment['category'] = td[6].text

        assignment['name'] = name
        assignment['status'] = status
        assignment['assigned'] = parse(td[4].text).isoformat()
        assignment['due'] = parse(td[5].text).isoformat()

        assignments.append(assignment)
        count += 1
        tr = course.find('tr', id='LOy_row' + str(count))

    if assignments:
        course_info['assignments'] = assignments
    course_info = __add_marking_periods_to__(course_info, __get_marking_periods__(course))
    return course_info

# parse the schedule page
def parse_schedule(schedule):
    schedule = BeautifulSoup(schedule, 'html.parser')
    courses = []
    count = 1
    tr = schedule.find('tr', id='LOy_row' + str(count))
    while tr is not None:
        td = tr.find_all('td', {'class': 'LO_field'})
        course = {}

        course['name'] = td[0].text
        data = td[1].text.split(' - ')
        if data[0].startswith('Period'):
            course['period'] = int(data[0][len("Period "):])
        course['teacher'] = data[-1]
        course['days'] = td[2].text
        course['room'] = td[3].text
        if td[4].text == 'Full Year':
            course['term'] = 'year'
        else:
            t = td[4].text.split(' ')
            course['term'] = t[0][0].lower() + t[1]

        courses.append(course)
        count += 1
        tr = schedule.find('tr', id='LOy_row' + str(count))
    return __add_marking_periods_to__({'courses':courses}, __get_marking_periods__(schedule))

# parse the calendar page
def parse_calendar(calendar):
    calendar = BeautifulSoup(calendar, 'html.parser')
    table = calendar.find('div', {'class': 'scroll_contents'}).find('table')
    tr = table.find_all('tr', recursive=False)
    tr.pop(0) #remove the row that has day names

    months = calendar.find('select', id='monthSelect1').find_all('option')
    years = calendar.find('select', id='yearSelect1').find_all('option')
    month, year = None, None
    for m in months:
        if 'selected' in m.attrs:
            month = int(m.attrs['value'])
            break
    for y in years:
        if 'selected' in y.attrs:
            year = int(y.attrs['value'])
            break

    events = []
    for r in tr:
        for d in r.find_all('td', recursive=False):
            if d.text.strip() == "":
                continue

            data = d.find('table').find_all('tr', recursive=False)
            if data[1].text.strip() == "":
                continue

            day = int(data[0].text)
            d = date(year, month, day).isoformat()
            for e in data[1].find_all('a'):
                name = e.text
                onclick = e.attrs['onclick']

                id = onclick[onclick.find('_id=') + 4:onclick.find('&year')]
                type = 'assignment' if onclick.find('assignment') >= 0 else 'event'
                events.append({
                    'id': id,
                    'name': name,
                    'type': type,
                    'date': d
                })

    return __add_marking_periods_to__({
            'events': events,
            'month': month,
            'year': year
        }, __get_marking_periods__(calendar))

def parse_calendar_event(calendar_event):
    calendar_event = BeautifulSoup(calendar_event, 'html.parser')
    d = {}

    tr = calendar_event.find('div', {'class': 'scroll_contents'}).find_all('tr')

    # if the event actually exists
    if tr[0].find_all('td')[1].text.replace('\u00a0', '') != '-':
        d['date'] = parse(tr[0].find_all('td')[1].text).date().isoformat()
        d['title'] = tr[1].find_all('td')[1].text

        # if the event is an assignment
        if tr[2].find_all('td')[0].text == 'Teacher':
            d['type'] = 'assignment'
            course = {}
            course['name'] = tr[3].find_all('td')[1].text
            data = tr[4].find_all('td')[1].text.split(' - ')
            course['period'] = int(data[0][len("Period "):])
            course['days'] = data[1]
            course['teacher'] = data[3]
            d['course'] = course
            start = 5
        else:
            d['type'] = 'event'
            start = 2

        d['school'] = tr[start].find_all('td')[1].text
        notes = tr[start + 1].find_all('td')[1].text.replace('\u00a0', ' ').strip()
        if notes != '-':
            d['notes'] = notes


    return d

# parse the demographic page (in student info)
def parse_demographic(demographic):
    demographic = BeautifulSoup(demographic, 'html.parser')
    d = {}

    tables = demographic.find('div', {'class': 'scroll_contents'}).find('table'), \
             demographic.find('table', {'class': 'remove_me'})

    td = tables[0].find('tr').find_all('td', recursive=False)
    picture_url = td[0].find('img').attrs['src']

    [s.extract() for s in td[1].find_all('small')]
    tr = td[1].find_all('tr')
    tr.pop()

    td = tr[0].find_all('td')
    d['name'] = td[0].text.replace('  ', ' ').strip()
    d['id'] = int(td[1].text)
    d['grade'] = int(td[2].text)

    td = tr[1].find_all('td')
    d['username'] = td[0].text
    d['pass_length'] = int(len(td[1].text))
    d['force_pass_change'] = False if td[2].text == 'No' else True

    td = tables[1].find_all('td')
    # d['birthday'] = parse(td[2].find(string=lambda text: isinstance(text, Comment)).strip()).date().isoformat()
    d['birthday'] = td[1].find(string=lambda text: isinstance(text, Comment))
    d['level'] = td[3].text
    d['gender'] = td[5].text.lower()
    d['nickname'] = td[7].text
    d['email'] = td[9].text
    d['locker'] = td[11].text
    d['locker_combo'] = td[13].text
    d['bus'] = td[15].text
    d['cumulative_file'] = td[17].text
    d['medical_record_status'] = td[19].text
    d['photo_auth'] = td[21].text
    d['student_mobile'] = td[23].text

    r = []
    for k in d:
        if d[k] == '' or d[k] == '-':
            r.append(k)
    for k in r:
        d.pop(k)

    if 'birthday' in d: d['birthday'] = parse(d['birthday'].strip()).date().isoformat()
    if 'level' in d: d['level'] = int(d['level'])
    if 'locker' in d: d['locker'] = int(d['locker'])
    if 'bus' in d and d['bus'] != '0':
        busses = d['bus'].split(' ')
        d['arrival_bus'] = int(busses[0])
        d['dismissal_bus'] = int(busses[1])
    if 'bus' in d: d.pop('bus')
    if 'cumulative_file' in d: d['cumulative_file'] = True if d['cumulative_file'] == 'Have file' else False
    if 'medical_record_status' in d: d['medical_record_status'] = \
        'need emergency form' if d['medical_record_status'] == 'Need emergency contact form' else 'unknown'
    if 'photo_auth' in d: d['photo_auth'] = True if d['photo_auth'] == 'Y' else False
    if 'student_mobile' in d: d['student_mobile'] = d['student_mobile'] \
                                                    .replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

    d = __add_marking_periods_to__(d, __get_marking_periods__(demographic))
    return d, picture_url

# parse the referrals page
def parse_referrals(referrals):
    pass #unimplemented