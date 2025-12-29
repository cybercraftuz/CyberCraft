from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Role


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    readonly_fields = ("username", "uuid")
    fieldsets = (
        (None, {"fields": ("username", "uuid", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "role", "skin", "avatar")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )
    list_display = ("username", "email", "uuid", "is_staff", "is_active")
    search_fields = ("username", "email", "uuid")
    ordering = ("id",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    model = Role
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
