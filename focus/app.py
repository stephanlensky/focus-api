#!flask/bin/python
import sys

from flask import Flask, jsonify, abort, request, make_response
import requests
import base64
from focus import parser
from focus.session import Session, find_session, session_expired
from calendar import monthrange
from datetime import date
import hmac
import hashlib
import urllib
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import re
from dateutil.parser import parse

app = Flask(__name__)
api_url = '/api/v2/'
tld = 'https://focus.asdnh.org/'
urls = {
    'login': tld + 'focus/index.php',
    'portal': tld + 'focus/Modules.php?modname=misc/Portal.php',
    'course_pre': tld + 'focus/Modules.php?modname=Grades/StudentGBGrades.php?course_period_id=',
    'schedule': tld + 'focus/Modules.php?modname=Scheduling/Schedule.php',
    'calendar_pre': tld + 'focus/Modules.php?modname=School_Setup/Calendar.php&',
    'event_pre': tld + 'focus/Modules.php?modname=School_Setup/Calendar.php&modfunc=detail&event_id=',
    'assignment_pre': tld + 'focus/Modules.php?modname=School_Setup/Calendar.php&modfunc=detail&assignment_id=',
    'demographic': tld + 'focus/Modules.php?modname=Students/Student.php',
    'absences': tld + 'focus/Modules.php?modname=Attendance/StudentSummary.php',
    'referrals': tld + 'focus/Modules.php?force_package=SIS&modname=Discipline/Referrals.php',
    'address': tld + 'focus/Modules.php?modname=Students/Student.php&include=Address',
    'final_grades': tld + 'focus/Modules.php?force_package=SIS&modname=Grades/StudentRCGrades.php',
    'api': tld + 'focus/API/APIEndpoint.php'
}

sessions = []

def sign_request(request):
    secret = 'e01c88dde89d9dc0cb59cec2e81e2602793ed282'.encode('ASCII')
    digest = '-{}-{}-{}'.format(request['accessID'], request['api'], request['method'])
    hash = hmac.new(secret, digest.encode('utf-8'), hashlib.sha1).hexdigest()
    request['signature'] = hash

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(401)
def unauthorized(error):
    return make_response(jsonify( { 'error': 'Invalid credentials' } ), 401)

@app.errorhandler(403)
def forbidden(error):
    return make_response(jsonify( { 'error': 'Forbidden' } ), 403)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

@app.errorhandler(500)
def internal_server_error(error):
    return make_response(jsonify( { 'error': 'Internal server error' } ), 500)


@app.route(api_url + 'session', methods = ['GET', 'POST', 'PUT'])
def session():
    if request.method == 'GET':
        s = find_session(request.cookies.get('PHPSESSID'), sessions)
        if s is None or session_expired(s):
            abort(403)
        return jsonify(s.dictify_for_user())
    elif request.method == 'POST':
        if not request.json or not 'username' in request.json or not 'password' in request.json:
            abort(400)

        data = {
            'login': 'true',
            'data': 'username={}&password={}'
                .format(request.json.get('username'), request.json.get('password'))
        }
        r = requests.post(urls['login'], data)
        if r.status_code == 200 and r.json()['success']:
            s = Session(request.json.get('username'), r.cookies['PHPSESSID'])
            sessions.append(s)
            resp = jsonify(s.dictify_for_user())
            resp.set_cookie('PHPSESSID', s.sess_id)
            return resp
        elif r.status_code == 200:
            abort(401)
        else:
            abort(500)

    elif request.method == 'PUT':
        s = find_session(request.cookies.get('PHPSESSID'), sessions)
        if s is None or session_expired(s):
            abort(403)
        if not request.json or not 'year' in request.json or not 'mp_id' in request.json \
                or not isinstance(request.json['year'], int) or not isinstance(request.json['mp_id'], int):
            abort(400)

        d = {'side_syear': request.json['year'], 'side_mp': request.json['mp_id']}
        valid_redirects = {
            'PORTAL': api_url + '{0,1}portal',
            'COURSE': api_url + '{0,1}courses\/[0-9]+',
            'SCHEDULE': api_url + '{0,1}schedule',
            'DEMOGRAPHIC': api_url + '{0,1}demographic'
        }

        if 'redirect' in request.json:
            redirect = request.json['redirect']
            picked = None
            for r in valid_redirects:
                p = re.compile(valid_redirects[r], re.IGNORECASE)
                m = p.match(redirect)
                if m is not None and len(m.string) == len(redirect):
                    picked = r
                    break

            if picked == 'COURSE':
                id = redirect.split('/')[1]
                r = requests.post(urls['course_pre'] + id, data=d, cookies=request.cookies)
                parsed = parser.parse_course(r.text)
            elif picked == 'SCHEDULE':
                r = requests.post(urls['schedule'], data=d, cookies=request.cookies)
                parsed = parser.parse_schedule(r.text)
            elif picked == 'DEMOGRAPHIC':
                r = requests.post(urls['demographic'], data=d, cookies=request.cookies)
                parsed = parser.parse_demographic(r.text)
            else:
                r = requests.post(urls['portal'], data=d, cookies=request.cookies)
                parsed = parser.parse_portal(r.text)
        else:
            r = requests.post(urls['portal'], data=d, cookies=request.cookies)
            parsed = parser.parse_portal(r.text)

        if r.status_code != 200:
            abort(500)
        return jsonify(parsed)


@app.route(api_url + 'portal', methods = ['GET'])
def portal():
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    r = requests.get(urls['portal'], cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    return jsonify(dict(parser.parse_portal(r.text), **parser.get_marking_periods(r.text)))

@app.route(api_url + 'courses', methods = ['GET'])
def courses():
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    r = requests.get(urls['portal'] + str(id), cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    portal = parser.parse_portal(r.text)
    d = {}
    d['courses'] = []
    for c in portal['courses']:
        r = requests.get(urls['course_pre'] + str(c['id']), cookies=request.cookies)
        if r.status_code != 200:
            abort(500)
        parsed = parser.parse_course(r.text)
        parsed['days'] = c['days']
        d['courses'].append(parsed)

    return jsonify(dict(d, **parser.get_marking_periods(r.text)))

@app.route(api_url + 'courses/<int:id>', methods = ['GET'])
def course(id):
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    r = requests.get(urls['course_pre'] + str(id), cookies=request.cookies)
    if r.status_code == 404:
        abort(404)
    elif r.status_code != 200:
        abort(500)
    return jsonify(parser.parse_course(r.text))

@app.route(api_url + 'schedule', methods = ['GET'])
def schedule():
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    r = requests.get(urls['schedule'], cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    return jsonify(dict(parser.parse_schedule(r.text), **parser.get_marking_periods(r.text)))

@app.route(api_url + 'calendar/<int:year>', methods = ['GET'])
def calendar_by_year(year):
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)

    query = "month={}&year={}".format(1, year)
    r = requests.get(urls['calendar_pre'] + query, cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    parsed = parser.parse_calendar(r.text)
    d = parsed
    d.pop('month')
    for i in range(2, 13):
        query = "month={}&year={}".format(i, year)
        r = requests.get(urls['calendar_pre'] + query, cookies=request.cookies)
        if r.status_code != 200:
            abort(500)
        parsed = parser.parse_calendar(r.text)
        d['events'] = d['events'] + parsed['events']
    return jsonify(dict(d), **parser.get_marking_periods(r.text))

@app.route(api_url + 'calendar/<int:year>/<int:month>', methods = ['GET'])
def calendar_by_month(year, month):
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    if not month > 0 or not month < 13:
        abort(400)

    query = "month={}&year={}".format(month, year)
    r = requests.get(urls['calendar_pre'] + query, cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    return jsonify(dict(parser.parse_calendar(r.text), **parser.get_marking_periods(r.text)))

@app.route(api_url + 'calendar/<int:year>/<int:month>/<int:day>', methods = ['GET'])
def calendar_by_day(year, month, day):
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    if month < 1 or month > 12 or day < monthrange(year, month)[0] or day > monthrange(year, month)[1]:
        abort(400)

    query = "month={}&year={}".format(month, year)
    r = requests.get(urls['calendar_pre'] + query, cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    parsed = parser.parse_calendar(r.text)
    parsed['events'] = [i for i in parsed['events'] if parse(i['date']).day == day]
    parsed['day'] = day
    return jsonify(dict(parsed, **parser.get_marking_periods(r.text)))

@app.route(api_url + 'calendar/assignments/<int:id>', methods = ['GET'])
def holiday(id):
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)

    r = requests.get(urls['assignment_pre'] + str(id), cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    ret = parser.parse_calendar_event(r.text)
    if ret:
        return jsonify(ret)
    abort(400)

@app.route(api_url + 'calendar/occasions/<int:id>', methods = ['GET'])
def assignment(id):
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)

    r = requests.get(urls['event_pre'] + str(id), cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    ret = parser.parse_calendar_event(r.text)
    if ret:
        return jsonify(ret)
    abort(400)

@app.route(api_url + 'demographic', methods = ['GET'])
def demographic():
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    r = requests.get(urls['demographic'], cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    ret = parser.parse_demographic(r.text)
    img = requests.get(urls['tld'] + ret[1].replace('../', ''), cookies=request.cookies)
    ret[0]['picture'] = base64.b64encode(img.content).decode('utf-8')
    return jsonify(dict(ret[0], **parser.get_marking_periods(r.text)))

@app.route(api_url + 'address', methods = ['GET'])
def address():
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    r = requests.get(urls['address'], cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    return jsonify(dict(parser.parse_address(r.text), **parser.get_marking_periods(r.text)))

@app.route(api_url + 'referrals', methods = ['GET'])
def referrals():
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    r = requests.get(urls['referrals'], cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    return jsonify(dict(parser.parse_referrals(r.text), **parser.get_marking_periods(r.text)))

@app.route(api_url + 'referrals/<int:id>', methods = ['GET'])
def referral(id):
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)
    r = requests.get(urls['referrals'], cookies=request.cookies)
    if r.status_code != 200:
        abort(500)

    parsed = parser.parse_referrals(r.text)
    target = None
    for ref in parsed['referrals']:
        if ref['id'] == id:
            target = ref
            break
    if target == None:
        abort(404)

    return jsonify(dict(target, **parser.get_marking_periods(r.text)))

@app.route(api_url + 'exams', methods = ['GET'])
def exams():
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)

    # calling the API does not work if you don't get this page first (focus plz)
    if not s.can_invoke_api:
        r = requests.get(urls['final_grades'], cookies=request.cookies)
        s.can_invoke_api = True
        s.student_id = parser.get_student_id(r.text)

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'accessID': s.student_id,
        'api': 'finalGrades',
        'method': 'requestGrades',
        'modname': 'Grades/StudentRCGrades.php',
        'arguments[]': 'all_SEM_exams',
        'arguments[1][**FIRST-REQUEST**]': 'true',
    }
    sign_request(data)

    r = requests.post(urls['api'], cookies=request.cookies, data=data, headers=headers)
    if r.status_code != 200:
        abort(500)
    r = r.json(); d = {'exams': []}

    for exam in r['result']['grades'].values():
        e = {}
        e['id'] = int(exam['id'])
        e['syear'] = int(exam['syear'])
        e['name'] = exam['course_title']
        e['affects_gpa'] = bool(exam['affects_gpa'])
        if e['affects_gpa']:
            e['gpa_points'] = float(exam['gpa_points'])
            e['weighted_gpa_points'] = float(exam['weighted_gpa_points'])
        e['teacher'] = exam['teacher'].split(', ')[1] + ' ' + exam['teacher'].split(', ')[0]
        e['course_id'] = int(exam['course_period_id'])
        e['course_num'] = exam['course_num']
        e['percent_grade'] = int(exam['percent_grade'])
        e['letter_grade'] = exam['grade_title']
        if exam['grad_subject_short_name']:
            e['subject'] = exam['grad_subject_short_name']
        if exam['credits'] and exam['credits_earned']:
            e['credits'] = float(exam['credits'])
            e['credits_earned'] = float(exam['credits_earned'])
        e['grade_level'] = int(exam['gradelevel_title'])
        e['last_updated'] = exam['last_updated_date']
        e['location'] = exam['location_title']
        e['semester'] = int(exam['_mp_title'].split(' ')[1])
        if exam['comment']:
            e['comment'] = exam['comment']

        if exam['last_updated_user'] in r['result']['defaults']['teacher']['1']:
            last_updated_by = r['result']['defaults']['teacher']['1'][exam['last_updated_user']]['title'].split(', ')
            e['last_updated_by'] = last_updated_by[1] + ' ' + last_updated_by[0]

        grade_scales = r['result']['defaults']['grade_scale']
        grade_scales.update(r['result']['domains']['grade_scale'])
        grade_scale_id = exam['grade_scale_id']
        for k in grade_scales:
            for id in grade_scales[k]:
                if id == grade_scale_id:
                    e['scale'] = grade_scales[k][id]['title']

        d['exams'].append(e)

    return jsonify(d)

@app.route(api_url + 'exams/<int:id>')
def exam(id):
    s = find_session(request.cookies.get('PHPSESSID'), sessions)
    if s is None or session_expired(s):
        abort(403)

    # calling the API does not work if you don't get this page first (focus plz)
    if not s.can_invoke_api:
        r = requests.get(urls['final_grades'], cookies=request.cookies)
        s.can_invoke_api = True
        s.student_id = parser.get_student_id(r.text)

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'accessID': s.student_id,
        'api': 'finalGrades',
        'method': 'requestGrades',
        'modname': 'Grades/StudentRCGrades.php',
        'arguments[]': 'all_SEM_exams',
        'arguments[1][**FIRST-REQUEST**]': 'true',
    }
    sign_request(data)

    r = requests.post(urls['api'], cookies=request.cookies, data=data, headers=headers)
    if r.status_code != 200:
        abort(500)
    r = r.json();
    d = {}

    for exam in r['result']['grades'].values():
        if int(exam['id']) == id:
            d['id'] = int(exam['id'])
            d['syear'] = int(exam['syear'])
            d['name'] = exam['course_title']
            d['affects_gpa'] = bool(exam['affects_gpa'])
            if d['affects_gpa']:
                d['gpa_points'] = float(exam['gpa_points'])
                d['weighted_gpa_points'] = float(exam['weighted_gpa_points'])
            d['teacher'] = exam['teacher'].split(', ')[1] + ' ' + exam['teacher'].split(', ')[0]
            d['course_id'] = int(exam['course_period_id'])
            d['course_num'] = exam['course_num']
            d['percent_grade'] = int(exam['percent_grade'])
            d['letter_grade'] = exam['grade_title']
            if exam['grad_subject_short_name']:
                d['subject'] = exam['grad_subject_short_name']
            if exam['credits'] and exam['credits_earned']:
                d['credits'] = float(exam['credits'])
                d['credits_earned'] = float(exam['credits_earned'])
            d['grade_level'] = int(exam['gradelevel_title'])
            d['last_updated'] = exam['last_updated_date']
            d['location'] = exam['location_title']
            d['semester'] = int(exam['_mp_title'].split(' ')[1])
            if exam['comment']:
                d['comment'] = exam['comment']

            if exam['last_updated_user'] in r['result']['defaults']['teacher']['1']:
                last_updated_by = r['result']['defaults']['teacher']['1'][exam['last_updated_user']]['title'].split(', ')
                d['last_updated_by'] = last_updated_by[1] + ' ' + last_updated_by[0]

            grade_scales = r['result']['defaults']['grade_scale']
            grade_scales.update(r['result']['domains']['grade_scale'])
            grade_scale_id = exam['grade_scale_id']
            for k in grade_scales:
                for id in grade_scales[k]:
                    if id == grade_scale_id:
                        d['scale'] = grade_scales[k][id]['title']
    if d:
        return jsonify(d)
    else:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)