from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
import re

User = get_user_model()

USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_]+$")


class UserSerializer(serializers.ModelSerializer):
    skin_url = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("username", "uuid", "skin_url", "avatar_url")
        read_only_fields = ("id", "username", "uuid")

    def get_skin_url(self, obj):
        request = self.context.get("request")
        if request and obj.skin and hasattr(obj.skin, "url"):
            return request.build_absolute_uri(obj.skin.url)
        return None

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if request and obj.avatar and hasattr(obj.avatar, "url"):
            return request.build_absolute_uri(obj.avatar.url)
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "password_confirm",
        )

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )

        user_data = attrs.copy()
        user_data.pop("password_confirm", None)

        password_validation.validate_password(
            attrs.get("password"), user=User(**user_data)
        )
        return attrs

    def validate_username(self, value):
        value = value.strip()

        if not USERNAME_REGEX.match(value):
            raise serializers.ValidationError(
                "Foydalanuvchi nomi faqat harflar, raqamlar va pastki chiziqdan iborat bo'lishi mumkin."
            )

        return value

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")

        user = User.objects.create_user(**validated_data, password=password)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data.get("new_password") != data.get("new_password_confirm"):
            raise serializers.ValidationError(
                {"new_password_confirm": "Yangi parollar mos kelmaydi."}
            )
        password_validation.validate_password(data.get("new_password"))
        return data


class LauncherLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
