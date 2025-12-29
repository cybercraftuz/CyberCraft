from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import LauncherToken


class LauncherTokenAuthentication(BaseAuthentication):
    keyword = "Launcher"

    def authenticate(self, request):
        header = request.headers.get("Authorization")
        if not header:
            return None

        try:
            keyword, token = header.split(" ", 1)
        except ValueError:
            return None

        if keyword != self.keyword:
            return None

        try:
            launcher_token = LauncherToken.objects.select_related("user").get(
                token=token,
                is_active=True,
            )
        except LauncherToken.DoesNotExist:
            raise AuthenticationFailed("Invalid launcher token")

        return (launcher_token.user, None)
