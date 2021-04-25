from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static

urlpatterns = [
    path('', include('apps.page.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('account/', include("apps.account.urls")),
    path('pdf/', include("apps.pdf.urls")),
    path('document/', include("apps.document.urls")),

    path('captcha/', include('captcha.urls')),

    # Admin paths
    path('grappelli/', include('grappelli.urls')),
    path('route66/', admin.site.urls),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
