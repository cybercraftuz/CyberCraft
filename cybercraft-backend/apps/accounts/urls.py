from django.urls import path
from . import views

urlpatterns = [
    # web
    path("register/", views.register),
    path("login/", views.login_view),
    path("logout/", views.logout_view),
    path("me/", views.me_view),
    path("change-password/", views.change_password),
    # launcher
    path("launcher/login/", views.launcher_login),
    path("launcher/me/", views.launcher_me),
    path("launcher/logout/", views.launcher_logout),
]
