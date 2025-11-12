# reportes/admin.py (Corregido con Flota)

from django.contrib import admin
from .models import User, Centro, ReporteDiario, Gasto, Chofer, Camion
from django.contrib.auth.admin import UserAdmin

# --- Inlines para ver la flota en el admin de Centro ---
class CamionInline(admin.TabularInline):
    model = Camion
    extra = 0
    fields = ('patente', 'estado', 'chofer_asignado')

class ChoferInline(admin.TabularInline):
    model = Chofer
    extra = 0
    fields = ('nombre', 'rut')

# --- Admin de Centro (Mejorado) ---
class CentroAdmin(admin.ModelAdmin):
    inlines = [ChoferInline, CamionInline] # Muestra choferes y camiones dentro del centro
    list_display = ('nombre',)

# --- Personalización del Admin de Usuario ---
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Datos de ACME', {'fields': ('rol', 'centro')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos de ACME', {'fields': ('rol', 'centro')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'rol', 'centro')

# --- Personalización del Admin de Reportes ---
class GastoInline(admin.TabularInline):
    model = Gasto
    extra = 0 

class ReporteDiarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'centro', 'autor', 'estado', 'recursos_disponibles', 'recursos_comprometidos', 'recursos_mantenimiento')
    list_filter = ('estado', 'centro', 'fecha')
    search_fields = ('centro__nombre', 'autor__username')
    inlines = [GastoInline]
    # Hacemos que los datos automáticos sean de solo lectura
    readonly_fields = ('recursos_disponibles', 'recursos_comprometidos', 'recursos_mantenimiento')

# --- Registramos todo ---
admin.site.register(User, CustomUserAdmin)
admin.site.register(Centro, CentroAdmin) # Usamos el admin mejorado
admin.site.register(ReporteDiario, ReporteDiarioAdmin)
admin.site.register(Gasto)
admin.site.register(Chofer) # Modelo nuevo
admin.site.register(Camion) # Modelo nuevo