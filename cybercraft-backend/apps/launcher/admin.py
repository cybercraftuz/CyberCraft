from django.contrib import admin
from .models import LauncherBuild
from .services import sha256_file


@admin.register(LauncherBuild)
class LauncherBuildAdmin(admin.ModelAdmin):
    list_display = ("version", "build_number", "is_active", "created_at")
    readonly_fields = ("sha256",)

    def save_model(self, request, obj, form, change):
        if obj.asar_file:
            obj.sha256 = sha256_file(obj.asar_file)

        if obj.is_active:
            LauncherBuild.objects.exclude(pk=obj.pk).update(is_active=False)

        super().save_model(request, obj, form, change)
