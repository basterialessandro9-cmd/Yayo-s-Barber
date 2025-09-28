from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.db.models import UniqueConstraint
from decimal import Decimal


class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    correo = models.EmailField(max_length=254, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Cliente(models.Model):
    ESTADOS = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    telefono = models.CharField(max_length=15)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activo')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.user.get_full_name() if self.user else "Cliente sin usuario"


class Barbero(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    telefono = models.CharField(max_length=15)
    comision = models.DecimalField(max_digits=5, decimal_places=2, default=50)  # % comisión

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class DiaLaboral(models.Model):
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name="dias_laborales")
    fecha = models.DateField()
    disponible = models.BooleanField(default=True)  # 🔹 nuevo campo

    class Meta:
        unique_together = ('barbero', 'fecha')
        ordering = ["fecha"]

    def __str__(self):
        estado = "Disponible" if self.disponible else "No disponible"
        return f"{self.barbero} - {self.fecha.strftime('%d/%m/%Y')} ({estado})"



class HorarioDisponible(models.Model):
    barbero = models.ForeignKey("Barbero", on_delete=models.CASCADE)
    dia_laboral = models.ForeignKey("DiaLaboral", on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    disponible = models.BooleanField(default=True)

    class Meta:
        ordering = ["fecha_hora"]

    def __str__(self):
        return f"{self.barbero} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"


class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion = models.PositiveIntegerField(help_text="Duración en minutos")

    def __str__(self):
        return f"{self.nombre} - ${self.precio} ({self.duracion} min)"


class QuienesSomos(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()

    def __str__(self):
        return self.titulo



class Cita(models.Model):
    ESTADOS = [
        ("confirmada", "Confirmada"),
        ("completada", "Completada"),
        ("cancelada", "Cancelada"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE)
    servicios = models.ManyToManyField(Servicio)
    horario = models.ForeignKey(HorarioDisponible, on_delete=models.CASCADE)
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_pagado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(max_length=20, choices=ESTADOS, default="confirmada")
    cliente_visible = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cliente'],
                name='unique_cita_por_dia',
                condition=models.Q(estado__in=['confirmada', 'completada'])
            )
        ]

    def __str__(self):
        return f"{self.cliente} - {self.inicio.strftime('%d/%m/%Y %H:%M')} ({self.estado})"

    # 🔹 Nuevo: cálculo dinámico de comisiones
@property
def total_barbero(self):
    config = Configuracion.objects.first()
    # usar comisión del barbero si existe, si no la global
    comision = self.barbero.comision if self.barbero.comision else (config.comision_global if config else 0)
    return (self.precio_total * Decimal(comision)) / Decimal(100)

@property
def total_admin(self):
    return self.precio_total - self.total_barbero




class Finanza(models.Model):
    cita = models.OneToOneField("Cita", on_delete=models.CASCADE, related_name="finanza")
    barbero = models.ForeignKey("Barbero", on_delete=models.CASCADE)
    ingreso_barbero = models.DecimalField(max_digits=10, decimal_places=2)
    ingreso_admin = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Finanza de cita {self.cita.id} - {self.barbero}"
    
    
class Configuracion(models.Model):
    comision_global = models.DecimalField(max_digits=5, decimal_places=2, default=30)  # porcentaje

    def __str__(self):
        return f"Configuración (comisión global: {self.comision_global}%)"