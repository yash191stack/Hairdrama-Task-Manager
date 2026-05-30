from .thread_local import set_current_user, clear_current_user

class ThreadLocalUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)
            
        response = self.get_response(request)
        clear_current_user()
        return response
