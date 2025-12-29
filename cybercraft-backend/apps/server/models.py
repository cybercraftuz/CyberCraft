from django.db import models
from apps.modpacks.models import ModPack
import uuid


class Server(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    server_image = models.ImageField(upload_to="server_image", blank=True)
    online_player = models.IntegerField(default=0)
    ip_address = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    repo = models.URLField(blank=True, null=True)
    version = models.CharField(max_length=20)
    ram = models.IntegerField(default=1024)
    port = models.IntegerField(unique=True, default=25565)
    modpack = models.ForeignKey(
        ModPack, on_delete=models.PROTECT, related_name="servers", null=True, blank=True
    )
    is_online = models.BooleanField(default=False)
    path = models.CharField(max_length=500)
    is_running = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pid = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.updated_at = models.DateTimeField(auto_now=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class ServerImage(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="servers/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.server.name}"
