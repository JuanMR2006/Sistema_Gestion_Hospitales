# appointments/models.py
import logging

from django.db import models

from medical.models import Medico, Paciente

logger = logging.getLogger(__name__)


class HorarioDisponible(models.Model):
    DIAS_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.IntegerField(choices=DIAS_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('medico', 'dia_semana', 'hora_inicio')
        ordering = ['dia_semana', 'hora_inicio']
        verbose_name = 'Horario Disponible'
        verbose_name_plural = 'Horarios Disponibles'

    def __str__(self):
        dia = dict(self.DIAS_CHOICES).get(self.dia_semana, '')
        return f'{self.medico} - {dia} {self.hora_inicio}'


class Cita(models.Model):
    PENDIENTE = 'PENDIENTE'
    CONFIRMADA = 'CONFIRMADA'
    CANCELADA = 'CANCELADA'
    COMPLETADA = 'COMPLETADA'

    ESTADO_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (CONFIRMADA, 'Confirmada'),
        (CANCELADA, 'Cancelada'),
        (COMPLETADA, 'Completada'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='citas')
    fecha_hora = models.DateTimeField()
    motivo = models.TextField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=PENDIENTE)
    notas_medico = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'

    def __str__(self):
        return (
            f'Cita: {self.paciente} con {self.medico} - '
            f'{self.fecha_hora.strftime("%d/%m/%Y %H:%M")}'
        )
