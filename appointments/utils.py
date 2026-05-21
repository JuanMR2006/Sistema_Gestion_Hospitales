# appointments/utils.py
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

_LABELS = {
    'creada': 'registrada',
    'PENDIENTE': 'marcada como pendiente',
    'CONFIRMADA': 'confirmada',
    'CANCELADA': 'cancelada',
    'COMPLETADA': 'completada',
}


def send_appointment_email(cita, accion):
    """
    Sends a notification email for a cita event.
    accion: 'creada' on creation, or a Cita.estado value on state change.
    Errors are logged and swallowed — never raise to callers.
    """
    try:
        label = _LABELS.get(accion, accion.lower())
        subject = f'Cita {label} — Sistema de Gestión Hospitalaria'
        body = (
            f'Estimado/a {cita.paciente.user.get_full_name()},\n\n'
            f'Le informamos que su cita ha sido {label}.\n\n'
            f'Médico: {cita.medico}\n'
            f'Fecha y hora: {cita.fecha_hora.strftime("%d/%m/%Y %H:%M")}\n'
            f'Motivo: {cita.motivo}\n\n'
            f'Sistema de Gestión Hospitalaria'
        )
        recipient = cita.paciente.user.email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hospital.com')
        if recipient:
            send_mail(subject, body, from_email, [recipient], fail_silently=False)
            logger.info(
                'Email enviado a %s por cita #%s (%s)', recipient, cita.pk, accion
            )
    except Exception as exc:
        logger.error('Error enviando email para cita #%s: %s', cita.pk, exc)
