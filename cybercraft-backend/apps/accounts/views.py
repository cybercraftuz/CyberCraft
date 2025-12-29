from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)

from django.contrib.auth import logout, get_user_model
from django.core.files.base import ContentFile

from .models import LauncherToken
from .auth_service import AuthService
from .authentication import LauncherTokenAuthentication
from .serializers import (
    LauncherLoginSerializer,
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
)

from PIL import Image

import io

User = get_user_model()


@api_view(["POST"])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {"detail": "registered", "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = AuthService.web_login(
        request,
        serializer.validated_data["username"],
        serializer.validated_data["password"],
    )

    return Response(
        {
            "detail": "logged in",
            "user": UserSerializer(user).data,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"detail": "logged out"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    old_password = serializer.validated_data["old_password"]
    if not user.check_password(old_password):
        return Response(
            {"old_password": ["Eski parol noto'g'ri."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_password = serializer.validated_data["new_password"]
    user.set_password(new_password)
    user.save()
    return Response({"detail": "Parol o'zgartirildi"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def launcher_login(request):
    serializer = LauncherLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user, token = AuthService.launcher_login(
        request,
        serializer.validated_data["username"],
        serializer.validated_data["password"],
    )

    return Response(
        {
            "token": token.token,
            "user": UserSerializer(user).data,
        }
    )


@api_view(["GET"])
@authentication_classes([LauncherTokenAuthentication])
def launcher_me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@authentication_classes([LauncherTokenAuthentication])
def launcher_logout(request):
    LauncherToken.objects.filter(
        user=request.user,
        is_active=True,
    ).update(is_active=False)

    return Response({"detail": "launcher_logged_out"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_skin(request):
    skin_file = request.FILES.get("skin")
    if not skin_file:
        return Response(
            {"detail": "Skin fayli topilmadi"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    user.skin.save("skin.png", skin_file)

    skin_img = Image.open(skin_file).convert("RGBA")
    avatar_crop = skin_img.crop((8, 8, 16, 16))

    buffer = io.BytesIO()
    avatar_crop.save(buffer, format="PNG")
    user.avatar.save("avatar.png", ContentFile(buffer.getvalue()))

    user.save()
    return Response({"detail": "Skin va avatar saqlandi"})
