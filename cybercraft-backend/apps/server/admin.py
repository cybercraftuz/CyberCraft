from django.contrib import admin
from .models import Server, ServerImage


@admin.register(Server)
class MinecraftServerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "version", "ram", "created_at")
    list_filter = ("version",)
    search_fields = ("name", "uuid")


admin.site.register(ServerImage)
