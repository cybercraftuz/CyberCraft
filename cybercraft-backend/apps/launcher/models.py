from django.db import models


class LauncherBuild(models.Model):
    version = models.CharField(max_length=20)
    build_number = models.PositiveIntegerField(unique=True)
    asar_file = models.FileField(upload_to="launcher/")
    sha256 = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.version} ({self.build_number})"
