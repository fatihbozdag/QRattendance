from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.login_page, name="login"),
    path("submit/", views.login_submit, name="login_submit"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),
    path("logout/", views.portal_logout, name="portal_logout"),
]
