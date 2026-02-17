from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.request_link, name="request_link"),
    path("submit/", views.request_link_submit, name="request_link_submit"),
    path("register/", views.register, name="register"),
    path("register/submit/", views.register_submit, name="register_submit"),
    path("login/<str:token>/", views.magic_login, name="magic_login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),
    path("logout/", views.portal_logout, name="portal_logout"),
]
