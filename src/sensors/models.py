from django.db import models
from django.utils import timezone


class EnviroProRecord(models.Model):
    fecha_hora = models.DateTimeField(unique=True, db_index=True)

    hum_s1_media = models.FloatField(null=True, blank=True)
    hum_s2_media = models.FloatField(null=True, blank=True)
    hum_s3_media = models.FloatField(null=True, blank=True)
    hum_s4_media = models.FloatField(null=True, blank=True)
    hum_s5_media = models.FloatField(null=True, blank=True)
    hum_s6_media = models.FloatField(null=True, blank=True)
    hum_s7_media = models.FloatField(null=True, blank=True)
    hum_s8_media = models.FloatField(null=True, blank=True)

    temp_s1_media = models.FloatField(null=True, blank=True)
    temp_s1_max = models.FloatField(null=True, blank=True)
    temp_s1_min = models.FloatField(null=True, blank=True)
    temp_s2_media = models.FloatField(null=True, blank=True)
    temp_s2_max = models.FloatField(null=True, blank=True)
    temp_s2_min = models.FloatField(null=True, blank=True)
    temp_s3_media = models.FloatField(null=True, blank=True)
    temp_s3_max = models.FloatField(null=True, blank=True)
    temp_s3_min = models.FloatField(null=True, blank=True)
    temp_s4_media = models.FloatField(null=True, blank=True)
    temp_s4_max = models.FloatField(null=True, blank=True)
    temp_s4_min = models.FloatField(null=True, blank=True)
    temp_s5_media = models.FloatField(null=True, blank=True)
    temp_s5_max = models.FloatField(null=True, blank=True)
    temp_s5_min = models.FloatField(null=True, blank=True)
    temp_s6_media = models.FloatField(null=True, blank=True)
    temp_s6_max = models.FloatField(null=True, blank=True)
    temp_s6_min = models.FloatField(null=True, blank=True)
    temp_s7_media = models.FloatField(null=True, blank=True)
    temp_s7_max = models.FloatField(null=True, blank=True)
    temp_s7_min = models.FloatField(null=True, blank=True)
    temp_s8_media = models.FloatField(null=True, blank=True)
    temp_s8_max = models.FloatField(null=True, blank=True)
    temp_s8_min = models.FloatField(null=True, blank=True)

    bateria_mv = models.IntegerField(null=True, blank=True)
    panel_solar_mv = models.IntegerField(null=True, blank=True)
    bateria_v = models.FloatField(null=True, blank=True)
    panel_solar_v = models.FloatField(null=True, blank=True)

    humedad_media = models.FloatField(null=True, blank=True)
    humedad_minima = models.FloatField(null=True, blank=True)
    humedad_maxima = models.FloatField(null=True, blank=True)
    temperatura_media = models.FloatField(null=True, blank=True)
    temperatura_minima = models.FloatField(null=True, blank=True)
    temperatura_maxima = models.FloatField(null=True, blank=True)

    source_file = models.CharField(max_length=255, blank=True)
    importado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["fecha_hora"]
        verbose_name = "registro EnviroPro"
        verbose_name_plural = "registros EnviroPro"

    def __str__(self):
        return f"EnviroPro {self.fecha_hora:%Y-%m-%d %H:%M}"
