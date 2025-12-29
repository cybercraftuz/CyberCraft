from django.contrib import admin
from .models import ModPack


@admin.register(ModPack)
class ModPackAdmin(admin.ModelAdmin):
    list_display = ("name", "mc_version", "loader", "updated_at")
    search_fields = ("name", "mc_version", "loader")
    list_filter = ("loader", "mc_version")
    ordering = ("-updated_at",)
