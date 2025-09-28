from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cita, Finanza, Configuracion

def crear_finanza(sender, instance, **kwargs):
    if instance.estado == "completada" and not hasattr(instance, "finanza"):
        # obtener comisión global (si no existe, usar 30%)
        config, _ = Configuracion.objects.get_or_create(id=1, defaults={"comision_global": 30})
        comision = config.comision_global  

        ingreso_barbero = instance.precio_total * (comision / 100)
        ingreso_admin = instance.precio_total - ingreso_barbero

        Finanza.objects.create(
            cita=instance,
            barbero=instance.barbero,
            ingreso_barbero=ingreso_barbero,
            ingreso_admin=ingreso_admin
        )
