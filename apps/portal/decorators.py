from functools import wraps

from django.shortcuts import redirect

from .services import get_logged_in_student_id


def portal_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not get_logged_in_student_id(request):
            return redirect("portal:login")
        return view_func(request, *args, **kwargs)
    return wrapper
