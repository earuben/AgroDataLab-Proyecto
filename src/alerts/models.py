from django.db import models


class Alert(models.Model):
    class AlertType(models.TextChoices):
        RELATIVE_DRYNESS = "sequedad_relativa", "Sequedad relativa"
        LOW_SENSOR_HUMIDITY = "humedad_sensor_baja", "Humedad baja en sensor"
        HUMIDITY_SHARP_RISE = "subida_brusca_humedad", "Subida brusca de humedad"
        HUMIDITY_SHARP_DROP = "caida_brusca_humedad", "Caida brusca de humedad"
        HIGH_TEMPERATURE = "temperatura_alta", "Temperatura alta"
        INCOHERENT_TEMPERATURE = "temperatura_incoherente", "Temperatura incoherente"
        LOW_BATTERY = "bateria_baja", "Bateria baja"
        LOW_SOLAR_PANEL = "panel_solar_bajo", "Panel solar bajo"
        STUCK_SENSOR = "sensor_bloqueado", "Sensor posiblemente bloqueado"
        TIME_GAP = "hueco_temporal", "Hueco temporal"

    class Level(models.TextChoices):
        INFO = "info", "Informativa"
        WARNING = "warning", "Aviso"
        CRITICAL = "critical", "Critica"

    class ManualStatus(models.TextChoices):
        PENDING = "pendiente", "Pendiente"
        REVIEWED = "revisada", "Revisada"
        DISCARDED = "descartada", "Descartada"

    record = models.ForeignKey(
        "sensors.EnviroProRecord",
        on_delete=models.CASCADE,
        related_name="alerts",
        null=True,
        blank=True,
    )
    fecha = models.DateTimeField(db_index=True)
    tipo = models.CharField(max_length=40, choices=AlertType.choices, db_index=True)
    nivel = models.CharField(max_length=20, choices=Level.choices, db_index=True)
    descripcion = models.TextField()
    variable_afectada = models.CharField(max_length=80)
    valor_detectado = models.FloatField(null=True, blank=True)
    recomendacion_texto = models.TextField()
    regla = models.CharField(max_length=120)
    estado_manual = models.CharField(
        max_length=20,
        choices=ManualStatus.choices,
        default=ManualStatus.PENDING,
        db_index=True,
    )
    observaciones = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "tipo"]
        constraints = [
            models.UniqueConstraint(
                fields=["record", "tipo", "regla"],
                name="unique_alert_by_record_type_rule",
            )
        ]
        verbose_name = "alerta"
        verbose_name_plural = "alertas"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha:%Y-%m-%d %H:%M}"


class Recommendation(models.Model):
    class Priority(models.TextChoices):
        LOW = "baja", "Baja"
        MEDIUM = "media", "Media"
        HIGH = "alta", "Alta"
        URGENT = "urgente", "Urgente"

    class Status(models.TextChoices):
        PENDING = "pendiente", "Pendiente"
        IN_PROGRESS = "en_revision", "En revision"
        DONE = "aplicada", "Revisada"
        DISCARDED = "descartada", "Descartada"

    titulo = models.CharField(max_length=160)
    descripcion = models.TextField()
    alerta_relacionada = models.ForeignKey(
        Alert,
        on_delete=models.SET_NULL,
        related_name="recommendations",
        null=True,
        blank=True,
    )
    prioridad = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    estado = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    creada_por = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        related_name="recommendations",
        null=True,
        blank=True,
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-actualizada_en", "-creada_en"]
        verbose_name = "recomendacion"
        verbose_name_plural = "recomendaciones"

    def __str__(self):
        return self.titulo
