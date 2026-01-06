from rest_framework import serializers
from .models import Server, ServerImage


class ServerImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerImage
        fields = ["id", "server", "image", "uploaded_at"]


class ServerSerializer(serializers.ModelSerializer):
    images = ServerImageSerializer(many=True, read_only=True)

    class Meta:
        model = Server
        fields = [
            "id",
            "name",
            "server_image",
            "description",
            "repo",
            "version",
            "created_at",
            "updated_at",
            "images",
        ]
