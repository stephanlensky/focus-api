import time

class Session(object):
    expire_time = None
    student_id = None
    can_invoke_api = False

    def __init__(self, user, sess_id):
        self.user = user
        self.sess_id = sess_id

    def dictify_for_user(self) -> dict:
        return {
            'timeout': self.expire_time,
            'username': self.user
        }

def is_valid_session(sess_id, sessions):
    s = find_session(sess_id, sessions)
    if s is not None and session_expired(s):
        return True
    return False

def find_session(sess_id, sessions: list) -> Session:
    for s in sessions:
        if s.sess_id == sess_id:
            return s
    return None

def session_expired(s):
    if s.expire_time and s.expire_time < time.time():
        return True
    return False