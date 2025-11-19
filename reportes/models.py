# reportes/models.py (COMPLETO Y CORREGIDO)

from django.db import models
from django.contrib.auth.models import AbstractUser

class Centro(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nombre

class User(AbstractUser):
    
    # --- ¡ROL CORREGIDO Y AÑADIDO! ---
    class Roles(models.TextChoices):
        DIRECTOR = 'DIRECTOR', 'Director General'
        OPERACIONES = 'OPERACIONES', 'Jefe de Operaciones'
        FINANZAS = 'FINANZAS', 'Área Financiera' # <-- ROL AÑADIDO
        ADMIN = 'ADMIN', 'Administrador Centro'
    
    rol = models.CharField(max_length=50, choices=Roles.choices, default=Roles.ADMIN)
    centro = models.ForeignKey(Centro, on_delete=models.SET_NULL, null=True, blank=True)

class Chofer(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE, related_name="choferes")
    
    def __str__(self):
        return f"{self.nombre} ({self.centro.nombre})"

class Camion(models.Model):
    class EstadoCamion(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        EN_RUTA = 'EN_RUTA', 'En Ruta'
        MANTENIMIENTO = 'MANTENIMIENTO', 'Mantenimiento'

    patente = models.CharField(max_length=8, unique=True, primary_key=True)
    estado = models.CharField(max_length=50, choices=EstadoCamion.choices, default=EstadoCamion.DISPONIBLE)
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE, related_name="camiones")
    chofer_asignado = models.OneToOneField(Chofer, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.patente} ({self.estado})"

class ReporteDiario(models.Model):
    class EstadoReporte(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador' 
        ENVIADO = 'ENVIADO', 'Enviado'
        PROCESADO = 'PROCESADO', 'Procesado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50, choices=EstadoReporte.choices, default=EstadoReporte.PROCESADO)
    
    recursos_disponibles = models.IntegerField(default=0)
    recursos_comprometidos = models.IntegerField(default=0)
    recursos_mantenimiento = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Reporte de {self.centro.nombre} - {self.fecha.date()}"

class Gasto(models.Model):
    class CategoriaGasto(models.TextChoices):
        COMBUSTIBLE = 'COMBUSTIBLE', 'Combustible'
        MANTENIMIENTO = 'MANTENIMIENTO', 'Mantenimiento'
        VIATICOS = 'VIATICOS', 'Viáticos'
        OTROS = 'OTROS', 'Otros'
    reporte = models.ForeignKey(ReporteDiario, related_name='gastos', on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=50, choices=CategoriaGasto.choices, default=CategoriaGasto.OTROS)
    def __str__(self):
        return f"{self.categoria} - ${self.monto}"