# dashboard/management/commands/seed_data.py
import random
from datetime import date, time, timedelta

from django.contrib.db import transaction
from django.core.management.base import BaseCommand
from django.utils import timezone

from appointments.models import Cita, HorarioDisponible
from medical.models import Especialidad, HistoriaClinica, Medico, Paciente
from users.models import CustomUser

_NOMBRES = [
    'Ana', 'Carlos', 'María', 'Jorge', 'Laura',
    'Pedro', 'Sofía', 'Diego', 'Valentina', 'Andrés',
    'Camila', 'Felipe', 'Isabella', 'Sebastián', 'Juliana',
    'Mateo', 'Daniela', 'Alejandro', 'Gabriela', 'Ricardo',
]
_APELLIDOS = [
    'García', 'Martínez', 'López', 'González', 'Rodríguez',
    'Hernández', 'Torres', 'Ramírez', 'Flores', 'Cruz',
    'Morales', 'Reyes', 'Jiménez', 'Ruiz', 'Díaz',
    'Pérez', 'Vargas', 'Castro', 'Núñez', 'Medina',
]
_MOTIVOS = [
    'Dolor de cabeza frecuente', 'Control mensual de presión arterial',
    'Revisión general de salud', 'Dolor abdominal agudo',
    'Tos persistente por más de 2 semanas', 'Fiebre alta sin causa aparente',
    'Revisión de resultados de laboratorio', 'Control de diabetes',
    'Vacunación de adultos', 'Consulta por alergia estacional',
    'Revisión cardiaca preventiva', 'Control post-operatorio',
    'Dolor en articulaciones', 'Problema de piel crónico',
    'Mareos frecuentes', 'Revisión pediátrica mensual',
    'Control de tensión arterial', 'Dolor de espalda lumbar',
]
_NOTAS_COMPLETADA = [
    'Paciente estable, seguimiento rutinario en 3 meses.',
    'Se ajustó medicación. Próxima cita en 30 días.',
    'Exámenes en orden. Sin novedades relevantes.',
    'Se indicó reposo y dieta blanda por 5 días.',
    'Resultados normales. Alta médica temporal.',
]


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema hospitalario (idempotente)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\nIniciando carga de datos de prueba...\n'
        ))
        with transaction.atomic():
            especialidades = self._crear_especialidades()
            self._crear_admin()
            medicos = self._crear_medicos(especialidades)
            pacientes = self._crear_pacientes()
            self._crear_horarios(medicos)
            self._crear_citas(medicos, pacientes)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✔  Seed completado exitosamente.\n'))
        self.stdout.write('   Credenciales de acceso:')
        self.stdout.write('   Admin:    admin / admin123')
        self.stdout.write('   Médicos:  doctor1..doctor5 / doctor123')
        self.stdout.write('   Pacientes: paciente1..paciente20 / paciente123\n')

    # ── Especialidades ─────────────────────────────────────────────────────

    def _crear_especialidades(self):
        nombres = [
            'Cardiología', 'Pediatría', 'Dermatología',
            'Neurología', 'Medicina General', 'Traumatología',
        ]
        creadas, especialidades = 0, []
        for nombre in nombres:
            esp, created = Especialidad.objects.get_or_create(nombre=nombre)
            if created:
                creadas += 1
            especialidades.append(esp)
        self.stdout.write(
            f'  Especialidades : {creadas} nuevas  ({len(especialidades)} total)'
        )
        return especialidades

    # ── Admin ───────────────────────────────────────────────────────────────

    def _crear_admin(self):
        if not CustomUser.objects.filter(username='admin').exists():
            CustomUser.objects.create_user(
                username='admin',
                email='admin@hospital.com',
                password='admin123',
                first_name='Admin',
                last_name='Sistema',
                role='ADMIN',
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write('  Admin          : creado  (admin / admin123)')
        else:
            self.stdout.write('  Admin          : ya existe')

    # ── Médicos ─────────────────────────────────────────────────────────────

    def _crear_medicos(self, especialidades):
        datos = [
            ('doctor1', 'Juan',    'García',    0),  # Cardiología
            ('doctor2', 'María',   'Rodríguez', 1),  # Pediatría
            ('doctor3', 'Carlos',  'López',     2),  # Dermatología
            ('doctor4', 'Ana',     'Martínez',  3),  # Neurología
            ('doctor5', 'Luis',    'Torres',    4),  # Medicina General
        ]
        creados, medicos = 0, []
        for n, (username, nombre, apellido, esp_idx) in enumerate(datos, start=1):
            if not CustomUser.objects.filter(username=username).exists():
                user = CustomUser.objects.create_user(
                    username=username,
                    email=f'{username}@hospital.com',
                    password='doctor123',
                    first_name=nombre,
                    last_name=apellido,
                    role='MEDICO',
                )
                medico, _ = Medico.objects.get_or_create(
                    user=user,
                    defaults={
                        'especialidad': especialidades[esp_idx],
                        'numero_licencia': f'LIC-000{n}',
                        'consultorio': f'Consultorio {n:02d}',
                    },
                )
                creados += 1
            else:
                user = CustomUser.objects.get(username=username)
                medico, _ = Medico.objects.get_or_create(
                    user=user,
                    defaults={
                        'especialidad': especialidades[esp_idx],
                        'numero_licencia': f'LIC-000{n}',
                    },
                )
            medicos.append(medico)
        self.stdout.write(
            f'  Médicos        : {creados} nuevos  ({len(medicos)} total)'
        )
        return medicos

    # ── Pacientes ───────────────────────────────────────────────────────────

    def _crear_pacientes(self):
        generos     = ['M','F','M','F','OTRO','M','F','M','F','M',
                       'F','M','F','F','M','M','F','M','F','F']
        blood_types = ['A+','O+','B+','AB+','A-','O-','B-','AB-',
                       'A+','O+','B+','A+','O+','O+','A-','B+',
                       'AB+','O+','A+','B-']
        ahora = timezone.now()
        creados, pacientes = 0, []

        for i in range(1, 21):
            username = f'paciente{i}'
            nombre   = _NOMBRES[i - 1]
            apellido = _APELLIDOS[i - 1]

            if not CustomUser.objects.filter(username=username).exists():
                user = CustomUser.objects.create_user(
                    username=username,
                    email=f'{username}@email.com',
                    password='paciente123',
                    first_name=nombre,
                    last_name=apellido,
                    role='PACIENTE',
                )
                # Distribuir registros en los últimos 12 meses para el chart
                dias_atras = random.randint(0, 365)
                CustomUser.objects.filter(pk=user.pk).update(
                    created_at=ahora - timedelta(days=dias_atras)
                )

                edad_dias  = random.randint(18 * 365, 70 * 365)
                fecha_nac  = (ahora - timedelta(days=edad_dias)).date()

                paciente, _ = Paciente.objects.get_or_create(
                    user=user,
                    defaults={
                        'fecha_nacimiento': fecha_nac,
                        'genero': generos[i - 1],
                        'blood_type': blood_types[i - 1],
                    },
                )
                HistoriaClinica.objects.get_or_create(paciente=paciente)
                creados += 1
            else:
                user = CustomUser.objects.get(username=username)
                paciente, _ = Paciente.objects.get_or_create(
                    user=user,
                    defaults={
                        'fecha_nacimiento': date(1990, 1, 1),
                        'genero': generos[i - 1],
                        'blood_type': blood_types[i - 1],
                    },
                )
                HistoriaClinica.objects.get_or_create(paciente=paciente)

            pacientes.append(paciente)

        self.stdout.write(
            f'  Pacientes      : {creados} nuevos  ({len(pacientes)} total)'
        )
        return pacientes

    # ── Horarios ────────────────────────────────────────────────────────────

    def _crear_horarios(self, medicos):
        turnos = [
            (time(8, 0),  time(12, 0)),
            (time(14, 0), time(17, 0)),
        ]
        creados = 0
        for medico in medicos:
            for dia in range(5):          # 0=Lunes … 4=Viernes
                for inicio, fin in turnos:
                    _, created = HorarioDisponible.objects.get_or_create(
                        medico=medico,
                        dia_semana=dia,
                        hora_inicio=inicio,
                        defaults={'hora_fin': fin, 'activo': True},
                    )
                    if created:
                        creados += 1
        self.stdout.write(f'  Horarios       : {creados} nuevos')

    # ── Citas ────────────────────────────────────────────────────────────────

    def _crear_citas(self, medicos, pacientes):
        existentes = Cita.objects.count()
        if existentes >= 50:
            self.stdout.write(
                f'  Citas          : ya existen {existentes}, omitiendo creación'
            )
            return

        ahora  = timezone.now()
        inicio = ahora - timedelta(days=90)
        fin    = ahora + timedelta(days=30)
        rango  = (fin - inicio).days

        # 40 % COMPLETADA · 20 % CONFIRMADA · 25 % PENDIENTE · 15 % CANCELADA
        estados = (
            ['COMPLETADA'] * 20 +
            ['CONFIRMADA'] * 10 +
            ['PENDIENTE']  * 13 +
            ['CANCELADA']  *  7
        )
        random.shuffle(estados)

        horas_turno = [8, 9, 10, 11, 14, 15, 16]
        creadas = 0

        for estado in estados:
            medico   = random.choice(medicos)
            paciente = random.choice(pacientes)
            hora     = random.choice(horas_turno)
            offset   = random.randint(0, rango)
            fecha_hora = inicio + timedelta(days=offset, hours=hora)

            # Las citas COMPLETADAS deben estar en el pasado
            if estado == 'COMPLETADA' and fecha_hora >= ahora:
                fecha_hora = ahora - timedelta(
                    days=random.randint(1, 90), hours=hora
                )

            Cita.objects.create(
                paciente=paciente,
                medico=medico,
                fecha_hora=fecha_hora,
                motivo=random.choice(_MOTIVOS),
                estado=estado,
                notas_medico=(
                    random.choice(_NOTAS_COMPLETADA) if estado == 'COMPLETADA' else ''
                ),
            )
            creadas += 1

        self.stdout.write(f'  Citas          : {creadas} nuevas')
