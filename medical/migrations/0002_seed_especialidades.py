from django.db import migrations


def seed_especialidades(apps, schema_editor):
    Especialidad = apps.get_model('medical', 'Especialidad')
    for nombre in ['Cardiología', 'Neumología', 'Neurología']:
        Especialidad.objects.get_or_create(nombre=nombre, defaults={'activa': True})


class Migration(migrations.Migration):

    dependencies = [
        ('medical', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_especialidades, migrations.RunPython.noop),
    ]
