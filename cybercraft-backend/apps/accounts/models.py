import re
import uuid
import secrets
import hashlib
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.conf import settings

USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_]+$")


def skin_upload_path(instance, filename):
    return f"skins/{instance.username}/skin.png"


def avatar_upload_path(instance, filename):
    return f"skins/{instance.username}/avatar.png"


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


def minecraft_offline_uuid(username: str) -> uuid.UUID:
    username = username.strip()
    username = username.lower()

    data = f"OfflinePlayer:{username}".encode("utf-8")
    md5 = hashlib.md5(data).digest()

    b = bytearray(md5)
    b[6] = (b[6] & 0x0F) | 0x30
    b[8] = (b[8] & 0x3F) | 0x80

    return uuid.UUID(bytes=bytes(b))


class User(AbstractUser):
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    uuid = models.UUIDField(
        editable=False,
        unique=True,
        blank=True,
        null=True,
    )

    skin = models.ImageField(upload_to=skin_upload_path, blank=True, null=True)
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        default="skins/default_avatar.png",
    )

    def clean(self):
        super().clean()

        if self.username and not USERNAME_REGEX.match(self.username):
            raise ValidationError(
                {
                    "username": "Foydalanuvchi nomi faqat harflar, raqamlar va pastki chiziqdan ( _ ) iborat bo'lishi mumkin."
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.username:
            self.uuid = minecraft_offline_uuid(self.username)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class LauncherToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="launcher_tokens",
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    @staticmethod
    def generate_token() -> str:
        return secrets.token_hex(32)

    def __str__(self):
        return f"LauncherToken(user={self.user.username})"
