# appointments/utils.py
import logging

from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

_SUBJECTS = {
    'creada':    '✅ Cita agendada - Hospital System',
    'confirmada': '✅ Cita confirmada - Hospital System',
    'cancelada':  '❌ Cita cancelada - Hospital System',
    'completada': '🏥 Consulta completada - Hospital System',
}


def send_appointment_email(cita, accion):
    """
    Sends a notification email for a cita event.
    accion: 'creada' | 'confirmada' | 'cancelada' | 'completada'
    Failures are logged as warnings and never propagated to the caller.
    """
    try:
        subject = _SUBJECTS.get(accion, f'Cita {accion} - Hospital System')
        fecha_formateada = cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')
        body = (
            f'Estimado/a {cita.paciente.user.get_full_name()},\n\n'
            f'Su cita ha sido {accion}.\n\n'
            f'Médico: {cita.medico.user.get_full_name()}\n'
            f'Especialidad: {cita.medico.especialidad}\n'
            f'Fecha y hora: {fecha_formateada}\n'
            f'Estado: {cita.get_estado_display()}\n'
            f'Motivo: {cita.motivo}\n\n'
            f'Saludos,\n'
            f'Hospital System'
        )
        recipient = cita.paciente.user.email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hospital.com')
        if recipient:
            send_mail(subject, body, from_email, [recipient], fail_silently=False)
            logger.info(
                'Email enviado a %s — cita #%s (%s)', recipient, cita.pk, accion
            )
    except Exception as exc:
        logger.warning(
            'No se pudo enviar email para cita #%s (accion=%s): %s',
            cita.pk, accion, exc,
        )
