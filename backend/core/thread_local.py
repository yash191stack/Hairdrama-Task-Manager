import threading

_locals = threading.local()

def get_current_user():
    return getattr(_locals, 'user', None)

def set_current_user(user):
    _locals.user = user

def clear_current_user():
    if hasattr(_locals, 'user'):
        del _locals.user
