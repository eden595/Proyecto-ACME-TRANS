# reportes/forms.py (AUDITADO Y CORREGIDO)

from django import forms
from django.core.exceptions import ValidationError
from .models import Gasto, Camion, Chofer
from django.db.models import Q

# --- Formulario de Gastos ---
class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['categoria', 'descripcion', 'monto']
        labels = {
            'categoria': 'Categoría',
            'descripcion': 'Descripción',
            'monto': 'Monto ($CLP)',
        }
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Detalle del gasto'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50000', 'type': 'number'}),
        }

# --- Formulario para Camiones (LOGICA BLINDADA) ---
class CamionForm(forms.ModelForm):
    class Meta:
        model = Camion
        fields = ['patente', 'estado', 'centro', 'chofer_asignado']
        labels = {
            'patente': 'Patente (Ej: AA-BB-11)',
            'estado': 'Estado',
            'centro': 'Centro',
            'chofer_asignado': 'Chofer (Solo disponibles)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Estilos base
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

        # LÓGICA DE FILTRADO DE CHOFERES
        # Solo mostramos choferes del mismo centro Y que no tengan camión asignado
        if 'instance' in kwargs and kwargs['instance'].centro:
            centro_id = kwargs['instance'].centro.id
            
            # Obtenemos choferes que NO tienen camión asignado (reverse relationship de OneToOne)
            choferes_libres = Chofer.objects.filter(centro_id=centro_id, camion__isnull=True)
            
            # Si estamos editando, debemos incluir al chofer que YA tiene este camión (si existe)
            if self.instance.pk and self.instance.chofer_asignado:
                chofer_actual = Chofer.objects.filter(pk=self.instance.chofer_asignado.pk)
                # Unimos los libres con el actual
                self.fields['chofer_asignado'].queryset = (choferes_libres | chofer_actual).distinct()
            else:
                self.fields['chofer_asignado'].queryset = choferes_libres
        else:
            # Si es nuevo y no se ha seleccionado centro (aunque tu vista pre-filtra, esto es seguridad extra)
            self.fields['chofer_asignado'].queryset = Chofer.objects.none()
        
        self.fields['chofer_asignado'].required = False

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get('estado')
        chofer_asignado = cleaned_data.get('chofer_asignado')

        # REGLA DE NEGOCIO 1: Si está EN RUTA, debe tener chofer
        if estado == Camion.EstadoCamion.EN_RUTA and not chofer_asignado:
            self.add_error('chofer_asignado', 'Un camión "En Ruta" OBLIGATORIAMENTE debe tener un chofer asignado.')
        
        # REGLA DE NEGOCIO 2: Si está EN RUTA, validar que el chofer no sea "fantasma" (extra seguridad)
        if estado == Camion.EstadoCamion.EN_RUTA and chofer_asignado:
            # Verificar si el chofer ya tiene otro camión (excluyendo este mismo)
            if hasattr(chofer_asignado, 'camion') and chofer_asignado.camion != self.instance:
                 self.add_error('chofer_asignado', f'El chofer {chofer_asignado.nombre} ya está conduciendo el camión {chofer_asignado.camion.patente}.')

        return cleaned_data

    def save(self, commit=True):
        camion = super().save(commit=False)

        # REGLA DE NEGOCIO 3: Limpieza automática
        # Si pasa a Disponible o Mantenimiento, desvinculamos al chofer automáticamente
        if camion.estado in [Camion.EstadoCamion.DISPONIBLE, Camion.EstadoCamion.MANTENIMIENTO]:
            camion.chofer_asignado = None
        
        if commit:
            camion.save()
        return camion


# --- Formulario para Choferes ---
class ChoferForm(forms.ModelForm):
    class Meta:
        model = Chofer
        fields = ['nombre', 'rut', 'centro']
        labels = {
            'nombre': 'Nombre Completo',
            'rut': 'RUT (Ej: 12.345.678-9)',
            'centro': 'Centro',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    # VALIDACIÓN EXTRA: Formato de RUT (Básico)
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        # Aquí podrías agregar un algoritmo de validación de RUT chileno real
        if len(rut) < 8:
            raise ValidationError("El RUT parece demasiado corto.")
        return rut