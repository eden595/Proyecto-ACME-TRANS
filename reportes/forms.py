# reportes/forms.py (COMPLETO Y CORREGIDO)

from django import forms
from .models import Gasto, Camion, Chofer

# --- Formulario de Gastos ---
class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['categoria', 'descripcion', 'monto']
        labels = {
            'categoria': 'Categoría del Gasto',
            'descripcion': 'Descripción',
            'monto': 'Monto ($CLP)',
        }
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Detalle del gasto (ej: Peaje ruta 5)'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '50000',
                'type': 'number' 
            }),
        }

# --- Formulario para Camiones ---
class CamionForm(forms.ModelForm):
    class Meta:
        model = Camion
        fields = ['patente', 'estado', 'centro', 'chofer_asignado']
        labels = {
            'patente': 'Patente (Ej: AA-BB-11)',
            'estado': 'Estado del Camión',
            'centro': 'Centro de Operación',
            'chofer_asignado': 'Chofer Asignado (Opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacemos que la lista de choferes se limite al centro seleccionado (si ya existe)
        # o que esté vacía si es un camión nuevo.
        # Esto requiere JS para funcionar dinámicamente, pero es un buen comienzo.
        if 'instance' in kwargs and kwargs['instance'].centro:
            self.fields['chofer_asignado'].queryset = Chofer.objects.filter(centro=kwargs['instance'].centro)
        else:
            self.fields['chofer_asignado'].queryset = Chofer.objects.none()

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        self.fields['chofer_asignado'].required = False


# --- Formulario para Choferes ---
class ChoferForm(forms.ModelForm):
    class Meta:
        model = Chofer
        fields = ['nombre', 'rut', 'centro']
        labels = {
            'nombre': 'Nombre Completo',
            'rut': 'RUT (Ej: 12345678-9)',
            'centro': 'Centro de Operación',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})