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
        # (El resto de tu método __init__ sigue igual)
        if 'instance' in kwargs and kwargs['instance'].centro:
            self.fields['chofer_asignado'].queryset = Chofer.objects.filter(centro=kwargs['instance'].centro)
        else:
            self.fields['chofer_asignado'].queryset = Chofer.objects.none()

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        self.fields['chofer_asignado'].required = False

    # --- ¡NUEVO MÉTODO AÑADIDO! ---
    def save(self, commit=True):
        camion = super().save(commit=False)

        # --- LÓGICA CORREGIDA ---
        # Si el estado es DISPONIBLE o MANTENIMIENTO, el chofer debe ser NULO.
        # El chofer solo se asigna si el estado es EN RUTA.
        if camion.estado == Camion.EstadoCamion.DISPONIBLE or camion.estado == Camion.EstadoCamion.MANTENIMIENTO:
            camion.chofer_asignado = None
        # --- FIN DE LA LÓGICA ---

        if commit:
            camion.save()


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