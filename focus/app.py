#!flask/bin/python
import sys

from flask import Flask, jsonify, abort, request, make_response
import requests
import base64
from focus import auth, parser
from calendar import monthrange
from datetime import date
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
}

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
        if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
            abort(403)
        d = {
            'username': auth.student_sessions(request.cookies.get['PHPSESSID'])[0],
            'timeout': auth.student_sessions(request.cookies.get['PHPSESSID'])[1] + auth.timeout
        }
        return jsonify(d)
    elif request.method == 'POST':
        if not request.json or not 'username' in request.json or not 'password' in request.json:
            abort(400)
        r = auth.login(request.json.get('username'), request.json.get('password'), urls['login'])
        if r == 401:
            abort(401)
        elif str(r).isdigit():
            abort(500)
        else:
            response = jsonify(r[1])
            response.set_cookie('PHPSESSID', value=r[0])
            return response
    elif request.method == 'PUT':
        if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
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
    if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
        abort(403)
    r = requests.get(urls['portal'], cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    return jsonify(parser.parse_portal(r.text))

@app.route(api_url + 'courses/<int:id>', methods = ['GET'])
def course(id):
    if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
        abort(403)
    r = requests.get(urls['course_pre'] + str(id), cookies=request.cookies)
    if r.status_code == 404:
        abort(404)
    elif r.status_code != 200:
        abort(500)
    return jsonify(parser.parse_course(r.text))

@app.route(api_url + 'schedule', methods = ['GET'])
def schedule():
    if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
        abort(403)
    r = requests.get(urls['schedule'], cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    return jsonify(parser.parse_schedule(r.text))

@app.route(api_url + 'calendar/<int:year>', methods = ['GET'])
def calendar_by_year(year):
    if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
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
    return jsonify(d)

@app.route(api_url + 'calendar/<int:year>/<int:month>', methods = ['GET'])
def calendar_by_month(year, month):
    if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
        abort(403)
    if not month > 0 or not month < 13:
        abort(400)

    query = "month={}&year={}".format(month, year)
    r = requests.get(urls['calendar_pre'] + query, cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    return jsonify(parser.parse_calendar(r.text))

@app.route(api_url + 'calendar/<int:year>/<int:month>/<int:day>', methods = ['GET'])
def calendar_by_day(year, month, day):
    if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
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
    return jsonify(parsed)

@app.route(api_url + 'calendar/assignments/<int:id>', methods = ['GET'])
def holiday(id):
    if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
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
    if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
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
    if not auth.is_valid_session(request.cookies.get('PHPSESSID')):
        abort(403)
    r = requests.get(urls['demographic'], cookies=request.cookies)
    if r.status_code != 200:
        abort(500)
    ret = parser.parse_demographic(r.text)
    img = requests.get(urls['tld'] + ret[1].replace('../', ''), cookies=request.cookies)
    ret[0]['picture'] = base64.b64encode(img.content).decode('utf-8')
    return jsonify(ret[0])


if __name__ == '__main__':
    app.run(debug=True)