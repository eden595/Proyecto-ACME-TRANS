# ACME_System/ACME_System/urls.py

from django.contrib import admin
from django.urls import path, include  # <-- Asegúrate de importar 'include'

# --- Imports para ver las imágenes (si las usamos) ---
from django.conf import settings
from django.conf.urls.static import static
# -------------------------------------------------

urlpatterns = [
    path('admin/', admin.site.urls),

    # Le decimos a Django que lea todas las URLs
    # desde nuestro archivo 'reportes/urls.py'
    path('', include('reportes.urls')),  # <-- AÑADE ESTA LÍNEA
]

# --- Configuración para archivos estáticos y media ---
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)