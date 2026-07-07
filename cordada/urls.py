from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuenta/", include("accounts.urls")),
    path("mercado/", include("market.urls")),
    path("comunidades/", include("communities.urls")),
    path("", include("feed.urls")),
    path("", include("activities.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
