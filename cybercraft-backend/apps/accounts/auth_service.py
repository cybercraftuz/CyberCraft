from django.contrib.auth import authenticate, login
from rest_framework.exceptions import AuthenticationFailed
from .models import LauncherToken


class AuthService:
    @staticmethod
    def authenticate_user(request, username: str, password: str):
        user = authenticate(request=request, username=username, password=password)
        if user is None:
            raise AuthenticationFailed("Invalid username or password")
        return user

    @staticmethod
    def web_login(request, username: str, password: str):
        user = AuthService.authenticate_user(request, username, password)
        login(request, user)
        return user

    @staticmethod
    def launcher_login(request, username: str, password: str):
        user = AuthService.authenticate_user(request, username, password)

        token = LauncherToken.objects.create(
            user=user,
            token=LauncherToken.generate_token(),
        )

        return user, token
