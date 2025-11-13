# reportes/views.py (COMPLETO Y CORREGIDO)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.db.models import Sum, Avg, Count, Q
from django.views.decorators.cache import never_cache
from django.contrib import messages 
from django.urls import reverse_lazy

# ¡NUEVAS IMPORTACIONES PARA CÁLCULOS DE FECHA Y JSON!
from django.utils import timezone
from datetime import timedelta
import json
from django.db.models.functions import TruncDate # <-- Import para agrupar por día
# ---

import csv
from django.http import HttpResponse

from .models import User, ReporteDiario, Gasto, Centro, Camion, Chofer
from .forms import GastoForm, CamionForm, ChoferForm

# --- VISTAS DE AUTENTICACIÓN ---
@never_cache 
def login_view(request):
    if request.user.is_authenticated: return redirect('panel')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username'); password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user); return redirect('panel') 
    else: form = AuthenticationForm()
    return render(request, 'reportes/login.html', {'form': form})
@login_required
def logout_view(request):
    logout(request); return redirect('login')

# --- VISTA ROUTER (¡CORREGIDA CON FINANZAS!) ---
@login_required
def panel_view(request):
    if request.user.rol == User.Roles.DIRECTOR: 
        return redirect('dashboard')
    elif request.user.rol == User.Roles.OPERACIONES:
        return redirect('flota_camion_list') 
    elif request.user.rol == User.Roles.FINANZAS: # <-- AÑADIDO
        return redirect('finanzas_dashboard')
    elif request.user.rol == User.Roles.ADMIN: 
        return redirect('entrada_datos')
    else: 
        return redirect('login')

# --- VISTA DEL "DIRECTOR GENERAL" (¡CORREGIDA Y SIMPLIFICADA!) ---
@login_required
@never_cache
def dashboard_view(request):
    if request.user.rol != User.Roles.DIRECTOR:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('panel')

    # --- 1. Lógica de KPIs (Últimos 30 días) ---
    hoy = timezone.now()
    hace_30_dias = hoy - timedelta(days=30)

    reportes_procesados_mes = ReporteDiario.objects.filter(
        estado=ReporteDiario.EstadoReporte.PROCESADO,
        fecha__gte=hace_30_dias
    )
    
    gastos_mes = Gasto.objects.filter(reporte__in=reportes_procesados_mes)
    
    total_gastos_mes = gastos_mes.aggregate(Sum('monto'))['monto__sum'] or 0
    
    total_camiones = Camion.objects.count()
    camiones_en_ruta = Camion.objects.filter(estado=Camion.EstadoCamion.EN_RUTA).count()

    # --- 2. Lógica Gráfico 1: Estado de Flota (Doughnut) ---
    flota_data_counts = Camion.objects.values('estado').annotate(conteo=Count('estado'))
    flota_labels = [Camion.EstadoCamion(d['estado']).label for d in flota_data_counts]
    flota_data = [d['conteo'] for d in flota_data_counts]

    # --- 3. Lógica Gráfico 2: Gastos del Mes por Categoría (Pie) ---
    gastos_por_categoria = gastos_mes.values('categoria') \
                                     .annotate(total=Sum('monto')) \
                                     .order_by('-total')
    
    gastos_cat_labels = [Gasto.CategoriaGasto(g['categoria']).label for g in gastos_por_categoria]
    gastos_cat_data = [int(g['total'] or 0) for g in gastos_por_categoria]

    # --- 4. Lógica "Gastos en el Tiempo" (ELIMINADA) ---
    # (Se eliminó la consulta para este gráfico a petición del usuario)

    # --- 5. Lógica de "Actividad Reciente" ---
    actividad_reciente = ReporteDiario.objects.annotate(
        total_reporte=Sum('gastos__monto')
    ).order_by('-fecha')[:5] 

    # ¡CORRECCIÓN DE LÓGICA! El .count() va al final.
    reportes_mes = reportes_procesados_mes.count()

    context = {
        'total_camiones': total_camiones,
        'camiones_en_ruta': camiones_en_ruta,
        'total_gastos_mes': f"{total_gastos_mes:,.0f}",
        'reportes_mes': reportes_mes,
        
        # Datos JSON para el frontend
        'flota_labels': json.dumps(flota_labels),
        'flota_data': json.dumps(flota_data),
        'gastos_cat_labels': json.dumps(gastos_cat_labels),
        'gastos_cat_data': json.dumps(gastos_cat_data),
        
        # (Se eliminan 'gastos_line_labels' y 'gastos_line_data')
        
        'actividad_reciente': actividad_reciente,
        'page_name': 'panel', 
    }
    return render(request, 'reportes/dashboard.html', context)

# --- VISTA DE REPORTES (PARA DIRECTOR) ---
@login_required
@never_cache
def reportes_generados_view(request):
    if request.user.rol != User.Roles.DIRECTOR:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('panel')
        
    filtro_centro_id = request.GET.get('centro'); filtro_fecha_inicio = request.GET.get('fecha_inicio'); filtro_fecha_fin = request.GET.get('fecha_fin')
    lista_reportes = ReporteDiario.objects.filter(estado=ReporteDiario.EstadoReporte.PROCESADO)
    if filtro_centro_id: lista_reportes = lista_reportes.filter(centro__id=filtro_centro_id)
    if filtro_fecha_inicio: lista_reportes = lista_reportes.filter(fecha__gte=filtro_fecha_inicio)
    if filtro_fecha_fin: lista_reportes = lista_reportes.filter(fecha__lte=filtro_fecha_fin)
    lista_reportes = lista_reportes.order_by('-fecha')
    todos_los_centros = Centro.objects.all()
    context = {
        'lista_reportes': lista_reportes, 'page_name': 'reportes',
        'todos_los_centros': todos_los_centros,
        'filtro_centro_id': filtro_centro_id,
        'filtro_fecha_inicio': filtro_fecha_inicio, 'filtro_fecha_fin': filtro_fecha_fin,
    }
    return render(request, 'reportes/reportes_generados.html', context)

# --- ¡NUEVA VISTA PARA FINANZAS! ---
@login_required
@never_cache
def finanzas_dashboard_view(request):
    # Esta vista es para el rol FINANZAS
    if request.user.rol not in [User.Roles.FINANZAS, User.Roles.DIRECTOR]:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('panel')
        
    filtro_centro_id = request.GET.get('centro'); filtro_fecha_inicio = request.GET.get('fecha_inicio'); filtro_fecha_fin = request.GET.get('fecha_fin')
    
    # El rol Finanzas ve todos los reportes PROCESADOS
    lista_reportes = ReporteDiario.objects.filter(estado=ReporteDiario.EstadoReporte.PROCESADO)
    
    if filtro_centro_id: lista_reportes = lista_reportes.filter(centro__id=filtro_centro_id)
    if filtro_fecha_inicio: lista_reportes = lista_reportes.filter(fecha__gte=filtro_fecha_inicio)
    if filtro_fecha_fin: lista_reportes = lista_reportes.filter(fecha__lte=filtro_fecha_fin)
    
    lista_reportes = lista_reportes.order_by('-fecha')
    todos_los_centros = Centro.objects.all()
    
    context = {
        'lista_reportes': lista_reportes, 
        'page_name': 'finanzas', # <-- Importante para el menú
        'todos_los_centros': todos_los_centros,
        'filtro_centro_id': filtro_centro_id,
        'filtro_fecha_inicio': filtro_fecha_inicio, 'filtro_fecha_fin': filtro_fecha_fin,
    }
    # Usamos un template nuevo que crearemos en el Paso 4
    return render(request, 'reportes/finanzas_dashboard.html', context)
# --- FIN DE NUEVA VISTA ---

@login_required
@never_cache
def configuracion_view(request):
    if request.user.rol != User.Roles.DIRECTOR: return redirect('panel')
    context = {'page_name': 'configuracion'}
    return render(request, 'reportes/configuracion.html', context)

@login_required
@never_cache
def flota_view(request):
    if request.user.rol != User.Roles.DIRECTOR: return redirect('panel')
    lista_camiones = Camion.objects.select_related('centro', 'chofer_asignado').all().order_by('centro__nombre', 'patente')
    context = {'lista_camiones': lista_camiones, 'page_name': 'flota'}
    return render(request, 'reportes/flota.html', context)

# --- VISTA ADMIN CENTRO ---
@login_required
@never_cache
def entrada_datos_view(request):
    if request.user.rol != User.Roles.ADMIN: return redirect('panel')
    GastoFormSet = modelformset_factory(Gasto, form=GastoForm, extra=0, min_num=1, can_delete=True)
    user_centro = request.user.centro
    recursos_disponibles = Camion.objects.filter(centro=user_centro, estado=Camion.EstadoCamion.DISPONIBLE).count()
    recursos_comprometidos = Camion.objects.filter(centro=user_centro, estado=Camion.EstadoCamion.EN_RUTA).count()
    recursos_mantenimiento = Camion.objects.filter(centro=user_centro, estado=Camion.EstadoCamion.MANTENIMIENTO).count()
    if request.method == 'POST':
        gasto_formset = GastoFormSet(request.POST, queryset=Gasto.objects.none())
        if gasto_formset.is_valid():
            reporte = ReporteDiario.objects.create(
                autor=request.user, centro=user_centro, 
                estado=ReporteDiario.EstadoReporte.PROCESADO,
                recursos_disponibles=recursos_disponibles,
                recursos_comprometidos=recursos_comprometidos,
                recursos_mantenimiento=recursos_mantenimiento
            )
            for gasto_form in gasto_formset:
                if gasto_form.cleaned_data and not gasto_form.cleaned_data.get('DELETE', False):
                    gasto = gasto_form.save(commit=False); gasto.reporte = reporte; gasto.save()
            messages.success(request, '¡Reporte enviado con éxito!')
            return redirect('panel')
    else:
        gasto_formset = GastoFormSet(queryset=Gasto.objects.none())
    context = {
        'gasto_formset': gasto_formset, 'page_name': 'entrada_datos',
        'recursos_disponibles': recursos_disponibles,
        'recursos_comprometidos': recursos_comprometidos,
        'recursos_mantenimiento': recursos_mantenimiento,
    }
    return render(request, 'reportes/entrada_datos.html', context)

# --- VISTA DE DETALLE (¡CORREGIDA CON FINANZAS!) ---
@login_required
@never_cache
def reporte_detalle_view(request, reporte_id):
    # ¡CORRECCIÓN DE PERMISOS!
    allowed_roles = [User.Roles.DIRECTOR, User.Roles.FINANZAS]
    if request.user.rol not in allowed_roles:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('panel')
        
    reporte = get_object_or_404(ReporteDiario, id=reporte_id)
    gastos = reporte.gastos.all()
    monto_total = gastos.aggregate(Sum('monto'))['monto__sum'] or 0
    total_items = gastos.count()
    context = {
        'reporte': reporte, 'gastos': gastos, 'page_name': 'reportes',
        'monto_total': monto_total, 'total_items': total_items,
    }
    return render(request, 'reportes/reporte_detalle.html', context)

# --- VISTA DE DESCARGA (¡CORREGIDA CON FINANZAS!) ---
@login_required
def descargar_reporte_csv(request, reporte_id):
    # ¡CORRECCIÓN DE PERMISOS!
    allowed_roles = [User.Roles.DIRECTOR, User.Roles.FINANZAS]
    if request.user.rol not in allowed_roles:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('panel')
        
    reporte = get_object_or_404(ReporteDiario, id=reporte_id)
    gastos = reporte.gastos.all() 
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="gastos_{reporte.centro.nombre}_{reporte.fecha}.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Reporte ID', 'Fecha', 'Centro', 'Categoría', 'Descripción', 'Monto'])
    for gasto in gastos:
        writer.writerow([
            reporte.id, reporte.fecha, reporte.centro.nombre,
            gasto.get_categoria_display(), gasto.descripcion, gasto.monto
        ])
    return response

# ---------------------------------------------------------
# VISTAS CRUD DE FLOTA (PARA OPERACIONES)
# (Estas vistas se mantienen sin cambios)
# ---------------------------------------------------------

@login_required
@never_cache
def flota_camion_list_view(request):
    if request.user.rol != User.Roles.OPERACIONES:
        messages.error(request, 'No tienes permisos para gestionar la flota.')
        return redirect('panel')
    lista_camiones = Camion.objects.select_related('centro', 'chofer_asignado').all().order_by('centro__nombre', 'patente')
    context = {
        'lista_camiones': lista_camiones,
        'page_name': 'flota_camiones', 
    }
    return render(request, 'reportes/flota_camion_list.html', context)

@login_required
@never_cache
def flota_camion_create_view(request):
    if request.user.rol != User.Roles.OPERACIONES:
        messages.error(request, 'No tienes permisos para gestionar la flota.')
        return redirect('panel')
    if request.method == 'POST':
        form = CamionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Camión creado con éxito!')
            return redirect('flota_camion_list')
    else:
        form = CamionForm()
    context = {
        'form': form, 'page_name': 'flota_camiones',
        'object_type': 'Camión', 'cancel_url': reverse_lazy('flota_camion_list')
    }
    return render(request, 'reportes/flota_form.html', context)

@login_required
@never_cache
def flota_camion_update_view(request, pk):
    if request.user.rol != User.Roles.OPERACIONES:
        messages.error(request, 'No tienes permisos para gestionar la flota.')
        return redirect('panel')
    camion = get_object_or_404(Camion, pk=pk)
    if request.method == 'POST':
        form = CamionForm(request.POST, instance=camion)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Camión {camion.patente} actualizado con éxito!')
            return redirect('flota_camion_list')
    else:
        form = CamionForm(instance=camion)
        form.fields['chofer_asignado'].queryset = Chofer.objects.filter(centro=camion.centro)
        
    context = {
        'form': form, 'page_name': 'flota_camiones',
        'object_type': 'Camión', 'cancel_url': reverse_lazy('flota_camion_list')
    }
    return render(request, 'reportes/flota_form.html', context)

@login_required
def flota_camion_delete_view(request, pk):
    if request.user.rol != User.Roles.OPERACIONES:
        messages.error(request, 'No tienes permisos para gestionar la flota.')
        return redirect('panel')
    camion = get_object_or_404(Camion, pk=pk)
    patente = camion.patente
    camion.delete()
    messages.success(request, f'Camión {patente} eliminado.')
    return redirect('flota_camion_list')

@login_required
@never_cache
def flota_chofer_list_view(request):
    if request.user.rol != User.Roles.OPERACIONES:
        messages.error(request, 'No tienes permisos para gestionar la flota.')
        return redirect('panel')
    lista_choferes = Chofer.objects.select_related('centro').all().order_by('centro__nombre', 'nombre')
    context = { 'lista_choferes': lista_choferes, 'page_name': 'flota_choferes' }
    return render(request, 'reportes/flota_chofer_list.html', context)

@login_required
@never_cache
def flota_chofer_create_view(request):
    if request.user.rol != User.Roles.OPERACIONES:
        messages.error(request, 'No tienes permisos para gestionar la flota.')
        return redirect('panel')
    if request.method == 'POST':
        form = ChoferForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Chofer creado con éxito!')
            return redirect('flota_chofer_list')
    else:
        form = ChoferForm()
    context = {
        'form': form, 'page_name': 'flota_choferes',
        'object_type': 'Chofer', 'cancel_url': reverse_lazy('flota_chofer_list')
    }
    return render(request, 'reportes/flota_form.html', context)

@login_required
@never_cache
def flota_chofer_update_view(request, pk):
    if request.user.rol != User.Roles.OPERACIONES:
        messages.error(request, 'No tienes permisos para gestionar la flota.')
        return redirect('panel')
    chofer = get_object_or_404(Chofer, pk=pk)
    if request.method == 'POST':
        form = ChoferForm(request.POST, instance=chofer)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Chofer {chofer.nombre} actualizado con éxito!')
            return redirect('flota_chofer_list')
    else:
        form = ChoferForm(instance=chofer)
    context = {
        'form': form, 'page_name': 'flota_choferes',
        'object_type': 'Chofer', 'cancel_url': reverse_lazy('flota_chofer_list')
    }
    return render(request, 'reportes/flota_form.html', context)

@login_required
def flota_chofer_delete_view(request, pk):
    if request.user.rol != User.Roles.OPERACIONES:
        messages.error(request, 'No tienes permisos para gestionar la flota.')
        return redirect('panel')
    chofer = get_object_or_404(Chofer, pk=pk)
    is_working = Camion.objects.filter(
        chofer_asignado=chofer, 
        estado=Camion.EstadoCamion.EN_RUTA
    ).exists()
    if is_working:
        messages.error(request, f'No se puede eliminar a {chofer.nombre} porque está asignado a un camión que está "En Ruta".')
    else:
        nombre_chofer = chofer.nombre
        chofer.delete()
        messages.success(request, f'Chofer {nombre_chofer} eliminado con éxito.')
    return redirect('flota_chofer_list')