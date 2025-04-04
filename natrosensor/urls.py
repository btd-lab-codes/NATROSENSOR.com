from django.conf import settings
from django.urls import path, re_path

from . import views

app_name = "natrosensor"
urlpatterns = [
    path("", views.welcome, name="welcome"),
    path("login", views.user_login, name="login"),
    path("logout", views.user_logout, name="logout"),
    path("signup", views.signup, name="signup"),
    path("verify/email", views.check_email, name="check_email"),
    path("verify/code", views.generate_code, name="generate_code"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("location", views.location, name="location"),
    path("process", views.process, name="process"),
    path("result", views.result, name="result"),
    path("records", views.records, name="records"),
    path("records/delete/<int:id>", views.delete_record, name="delete_record"),
    path("schedule", views.schedule, name="schedule"),
    path("schedule/view", views.show_schedule, name="show_schedule"),
    path("schedule/delete/<int:id>", views.delete_schedule, name="delete_schedule"),
    path("about", views.about, name="about"),
    path("profile", views.profile, name="profile"),
    path("settings", views.settings, name="settings"),
    path("test", views.test, name="test"),
    re_path(r"^.*/$", views.not_found, name="not_found"),
]