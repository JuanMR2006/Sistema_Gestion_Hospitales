import logging

from django.contrib.auth.models import AbstractUser
from django.db import models

logger = logging.getLogger(__name__)


class CustomUser(AbstractUser):
    ADMIN = 'ADMIN'
    MEDICO = 'MEDICO'
    PACIENTE = 'PACIENTE'

    ROLE_CHOICES = [
        (ADMIN, 'Administrador'),
        (MEDICO, 'Médico'),
        (PACIENTE, 'Paciente'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=PACIENTE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    photo = models.ImageField(upload_to='users/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @property
    def is_medico(self):
        return self.role == self.MEDICO

    @property
    def is_paciente(self):
        return self.role == self.PACIENTE

    def __str__(self):
        full_name = self.get_full_name().strip()
        display = full_name if full_name else self.username
        return f'{display} ({self.get_role_display()})'
