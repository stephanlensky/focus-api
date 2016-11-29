#!flask/bin/python
import requests
import sys

student_sessions = {}
login_url = "https://focus.asdnh.org/focus/index.php"

def login(u, p):
    data = {
        'login': 'true',
        'data': 'username=' + u + '&password=' + p
    }
    r = requests.post(login_url, data)
    if r.json()['success']:
        student_sessions[r.cookies['PHPSESSID']] = u
        return True, r.cookies['PHPSESSID']
    else:
        return False,


def is_valid_session(sess_id):
    if sess_id in student_sessions:
        return True
    return False
