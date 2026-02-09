"""
URL configuration for Cargo Platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.views import CustomPasswordChangeView

urlpatterns = [
    # Override admin password change view
    path('admin/password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.api.v1.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
