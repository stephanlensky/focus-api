#!flask/bin/python
import requests
import sys
import time

student_sessions = {}


def login(u, p, url):
    data = {
        'login': 'true',
        'data': 'username=' + u + '&password=' + p
    }
    r = requests.post(url, data)
    if r.json()['success']:
        student_sessions[r.cookies['PHPSESSID']] = u, time.time()
        return r.cookies['PHPSESSID']
    else:
        return ()


def is_valid_session(sess_id):
    if sess_id in student_sessions and time.time() < student_sessions[sess_id][1] + (20 * 60):
        student_sessions[sess_id] = student_sessions[sess_id][0], time.time()
        return True
    else:
        student_sessions.pop(sess_id)
        return False
