# dashboard/charts.py
import logging
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import ExtractWeekDay, TruncMonth
from django.http import JsonResponse
from django.utils import timezone

from appointments.models import Cita
from medical.models import Paciente

logger = logging.getLogger(__name__)

_NOMBRES_MES = [
    'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
]


@login_required
def citas_por_especialidad(request):
    try:
        months = int(request.GET.get('months', 6))
    except (ValueError, TypeError):
        months = 6
    months = max(1, min(months, 12))

    fecha_inicio = timezone.now() - timedelta(days=months * 30)

    data = (
        Cita.objects.filter(fecha_hora__gte=fecha_inicio)
        .values('medico__especialidad__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    labels = [d['medico__especialidad__nombre'] or 'Sin especialidad' for d in data]
    counts = [d['total'] for d in data]

    return JsonResponse({'labels': labels, 'data': counts, 'months': months})


@login_required
def pacientes_por_mes(request):
    ahora = timezone.now()

    # Primer día del mes que inicia la ventana de 12 meses
    base = ahora.year * 12 + ahora.month - 11
    first_year = (base - 1) // 12
    first_month = base - first_year * 12
    fecha_inicio = timezone.make_aware(datetime(first_year, first_month, 1))

    raw = (
        Paciente.objects.filter(user__created_at__gte=fecha_inicio)
        .annotate(mes=TruncMonth('user__created_at'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    counts_by_month = {(d['mes'].year, d['mes'].month): d['total'] for d in raw}

    labels = []
    data = []
    for i in range(12):
        total_months = ahora.year * 12 + ahora.month - 11 + i
        year = (total_months - 1) // 12
        month = total_months - year * 12
        labels.append(f"{_NOMBRES_MES[month - 1]} {year}")
        data.append(counts_by_month.get((year, month), 0))

    return JsonResponse({'labels': labels, 'data': data})


@login_required
def citas_por_estado(request):
    estados = [
        ('PENDIENTE',  'Pendiente',  '#ffc107'),
        ('CONFIRMADA', 'Confirmada', '#198754'),
        ('CANCELADA',  'Cancelada',  '#dc3545'),
        ('COMPLETADA', 'Completada', '#0d6efd'),
    ]
    labels = [e[1] for e in estados]
    data   = [Cita.objects.filter(estado=e[0]).count() for e in estados]
    colors = [e[2] for e in estados]

    return JsonResponse({'labels': labels, 'data': data, 'colors': colors})


@login_required
def citas_por_dia_semana(request):
    # ExtractWeekDay: 1=Domingo, 2=Lunes, 3=Martes, ..., 7=Sábado
    # Conversión a 0=Lun, 1=Mar, 2=Mié, 3=Jue, 4=Vie, 5=Sáb, 6=Dom:
    # índice = (django_day - 2) % 7
    raw = (
        Cita.objects.annotate(dia=ExtractWeekDay('fecha_hora'))
        .values('dia')
        .annotate(total=Count('id'))
        .order_by('dia')
    )

    counts = [0] * 7
    for d in raw:
        idx = (d['dia'] - 2) % 7
        counts[idx] = d['total']

    labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

    return JsonResponse({'labels': labels, 'data': counts})
