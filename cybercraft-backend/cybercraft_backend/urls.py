from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/servers/", include("apps.server.api_urls")),
    path("servers/", include("apps.server.urls")),
    path("api/", include("apps.launcher.urls")),
    path("health/", health_check),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
