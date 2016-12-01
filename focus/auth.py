#!flask/bin/python
import requests
import sys
import time

student_sessions = {}
timeout = 20 * 60 # in seconds


def login(u, p, url):
    data = {
        'login': 'true',
        'data': 'username=' + u + '&password=' + p
    }
    r = requests.post(url, data)
    if r.status_code != 200:
        return r.status_code
    if r.json()['success']:
        student_sessions[r.cookies['PHPSESSID']] = u, time.time()
        return {'PHPSESSID': r.cookies['PHPSESSID']}
    else:
        return None


def is_valid_session(sess_id):
    if sess_id in student_sessions and time.time() < student_sessions[sess_id][1] + timeout:
        student_sessions[sess_id] = student_sessions[sess_id][0], time.time()
        return True
    elif sess_id in student_sessions:
        student_sessions.pop(sess_id)
    return False
