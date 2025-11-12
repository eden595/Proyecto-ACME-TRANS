# reportes/urls.py (COMPLETO Y CORREGIDO)

from django.urls import path
from . import views

urlpatterns = [
    # URLs de Autenticación y Router de Roles
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('panel/', views.panel_view, name='panel'),

    # URLs del "Director General"
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('reportes/', views.reportes_generados_view, name='reportes'),
    path('configuracion/', views.configuracion_view, name='configuracion'),
    path('flota/', views.flota_view, name='flota'),
    
    # URLs del "Jefe de Operaciones"
    # ¡URL 'finanzas/' ELIMINADA!
    
    # --- CRUD de Flota ---
    path('operaciones/flota/camiones/', views.flota_camion_list_view, name='flota_camion_list'),
    path('operaciones/flota/camiones/crear/', views.flota_camion_create_view, name='flota_camion_create'),
    path('operaciones/flota/camiones/editar/<str:pk>/', views.flota_camion_update_view, name='flota_camion_update'),
    path('operaciones/flota/camiones/eliminar/<str:pk>/', views.flota_camion_delete_view, name='flota_camion_delete'),
    
    path('operaciones/flota/choferes/', views.flota_chofer_list_view, name='flota_chofer_list'),
    path('operaciones/flota/choferes/crear/', views.flota_chofer_create_view, name='flota_chofer_create'),
    path('operaciones/flota/choferes/editar/<int:pk>/', views.flota_chofer_update_view, name='flota_chofer_update'),
    path('operaciones/flota/choferes/eliminar/<int:pk>/', views.flota_chofer_delete_view, name='flota_chofer_delete'),
    # --- FIN CRUD ---

    # URLs del "Administrador Centro"
    path('entrada-datos/', views.entrada_datos_view, name='entrada_datos'),
    
    # URLs de Acciones
    path('reporte/detalle/<int:reporte_id>/', views.reporte_detalle_view, name='reporte_detalle'),
    path('reporte/descargar/<int:reporte_id>/', views.descargar_reporte_csv, name='descargar_reporte'),
]