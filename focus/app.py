#!flask/bin/python
import sys

from flask import Flask, jsonify, abort, request, make_response
import requests
import base64
from focus import auth, parser

app = Flask(__name__)
api_url = '/api/v1/'
urls = {
    'tld': 'https://focus.asdnh.org/',
    'portal': 'https://focus.asdnh.org/focus/Modules.php?modname=misc/Portal.php',
    'course_pre': 'https://focus.asdnh.org/focus/Modules.php?modname=Grades/StudentGBGrades.php?course_period_id=',
    'schedule': 'https://focus.asdnh.org/focus/Modules.php?modname=Scheduling/Schedule.php',
    'calendar_pre': 'https://focus.asdnh.org/focus/Modules.php?modname=School_Setup/Calendar.php&',
    'demographic': 'https://focus.asdnh.org/focus/Modules.php?modname=Students/Student.php',
    'absences': 'https://focus.asdnh.org/focus/Modules.php?modname=Attendance/StudentSummary.php',
}

@app.errorhandler(400)
def not_found(error):
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


@app.route(api_url)
def index():
    return "Hello, World!"


@app.route(api_url + 'login', methods = ['POST'])
def login():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        abort(400)
    r = auth.login(request.json.get('username'), request.json.get('password'))
    if r:
        return jsonify( { 'PHPSESSID':r } )
    else:
        abort(401)

@app.route(api_url + 'marking_period', methods = ['POST'])
def set_marking_period():
    if request.cookies.get('PHPSESSID') not in auth.student_sessions:
        abort(403)
    if not request.args.get('year') or not request.args.get('mp'):
        abort(400)
    year, mp = request.args.get('year'), request.args.get('mp')
    if not year.isdigit() or not mp.isdigit():
        abort(400)
    year, mp = int(year), int(mp)

    r = requests.post(urls['portal'], data={'side_syear': year, 'side_mp': mp}, cookies=request.cookies)
    return jsonify(parser.parse_portal(r.text))


@app.route(api_url + 'portal', methods = ['GET'])
def get_portal():
    if request.cookies.get('PHPSESSID') not in auth.student_sessions:
        abort(403)
    r = requests.get(urls['portal'], cookies=request.cookies)
    return jsonify(parser.parse_portal(r.text))

@app.route(api_url + 'course/<int:course_id>', methods = ['GET'])
def get_course(course_id):
    if request.cookies.get('PHPSESSID') not in auth.student_sessions:
        abort(403)
    r = requests.get(urls['course_pre'] + str(course_id), cookies=request.cookies)
    if r.status_code == 404:
        abort(404)
    return jsonify(parser.parse_course(r.text))

@app.route(api_url + 'schedule', methods = ['GET'])
def get_schedule():
    if request.cookies.get('PHPSESSID') not in auth.student_sessions:
        abort(403)
    r = requests.get(urls['schedule'], cookies=request.cookies)
    return jsonify(parser.parse_schedule(r.text))

@app.route(api_url + 'calendar', methods = ['GET'])
def get_calendar():
    if request.cookies.get('PHPSESSID') not in auth.student_sessions:
        abort(403)
    if not request.args.get('month') or not request.args.get('year'):
        abort(400)
    month, year = request.args.get('month'), request.args.get('year')
    if not month.isdigit() or not year.isdigit():
        abort(400)
    if not int(month) > 0 or not int(month) < 13:
        abort(400)

    r = requests.get(urls['calendar_pre'] + 'month=' + month + '&year=' + year, cookies=request.cookies)
    return jsonify(parser.parse_calendar(r.text))

@app.route(api_url + 'demographic', methods = ['GET'])
def get_demographic():
    if request.cookies.get('PHPSESSID') not in auth.student_sessions:
        abort(403)
    r = requests.get(urls['demographic'], cookies=request.cookies)
    ret = parser.parse_demographic(r.text)
    img = requests.get(urls['tld'] + ret[1].replace('../', ''), cookies=request.cookies)
    ret[0]['picture'] = base64.b64encode(img.content).decode('utf-8')
    return jsonify(ret[0])

if __name__ == '__main__':
    app.run(debug=True)