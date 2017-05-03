import time

class Session(object):
    timeout = 20 * 60 # in seconds
    student_id = None
    can_invoke_api = False

    def __init__(self, user, sess_id):
        self.user = user
        self.sess_id = sess_id
        self.last_accessed = time.time()

    def __get_expires(self):
        t = self.last_accessed + self.timeout
        self.last_accessed = time.time()
        return t

    def dictify_for_user(self) -> dict:
        return {
            'timeout': self.last_accessed + self.timeout,
            'username': self.user
        }

    expire_time = property(__get_expires)

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
    if s.expire_time < time.time():
        return True
    return False