from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.views.static import serve

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("salud/", views.health, name="health"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "privacidad/",
        TemplateView.as_view(template_name="legal/privacy.html"),
        name="privacy",
    ),
    path(
        "terminos/",
        TemplateView.as_view(template_name="legal/terms.html"),
        name="terms",
    ),
    path("cuenta/", include("accounts.urls")),
    path("mercado/", include("market.urls")),
    path("comunidades/", include("communities.urls")),
    path("", include("feed.urls")),
    path("", include("activities.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # En el plan gratuito de Render no hay CDN ni almacenamiento externo,
    # así que los archivos subidos se sirven desde Django. Es suficiente
    # para el alcance del proyecto; con más tráfico se movería a S3 o similar.
    urlpatterns += [
        path(
            "media/<path:path>",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
