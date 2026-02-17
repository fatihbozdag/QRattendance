from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("<uuid:qr_token>/", views.scan_landing, name="scan_landing"),
    path("<uuid:qr_token>/submit/", views.submit_attendance, name="submit_attendance"),
]
