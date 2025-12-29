from django.db import models


class ModPack(models.Model):
    LOADER_CHOICES = [
        ("forge", "Forge"),
        ("fabric", "Fabric"),
        ("neoforge", "NeoForge"),
    ]
    name = models.CharField(max_length=100, unique=True)
    mc_version = models.CharField(max_length=20)
    loader = models.CharField(max_length=20, choices=LOADER_CHOICES)
    path = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
