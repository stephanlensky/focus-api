import time

class Session(object):
    time_limit = 20 * 60 # in seconds
    student_id = None
    can_invoke_api = False


    def __init__(self, user, sess_id):
        self.user = user
        self.sess_id = sess_id
        self.last_accessed = time.time()

    def __get_timeout(self):
        return self.last_accessed + self.time_limit

    def expired(self):
        return self.__get_timeout() < time.time()

    timeout = property(__get_timeout)

def is_valid_session(sess_id, sessions):
    s = find_session(sess_id, sessions)
    if s is not None and not s.expired():
        return True
    return False

def find_session(sess_id, sessions: list) -> Session:
    for s in sessions:
        if s.sess_id == sess_id:
            return s
    return None