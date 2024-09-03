from django.urls import path

from . import views

app_name = "natrosensor"
urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.user_login, name="login"),
    path("logout", views.user_logout, name="logout"),
    path("signup", views.signup, name="signup"),
    path("verify", views.verify, name="verify"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("location", views.location, name="location"),
    path("process", views.process, name="process"),
    path("autolocate", views.autolocate, name="autolocate"),
    path("result", views.result, name="result"),
    path("records", views.records, name="records"),
    path("schedule", views.schedule, name="schedule"),
    path("about", views.about, name="about"),
    path("profile", views.profile, name="profile"),
    path("settings", views.settings, name="settings"),
    path("test", views.test, name="test")
]