from django.contrib import admin

from .models import EnviroProRecord


@admin.register(EnviroProRecord)
class EnviroProRecordAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_hora",
        "humedad_media",
        "temperatura_media",
        "bateria_mv",
        "panel_solar_mv",
    )
    list_filter = ("source_file",)
    search_fields = ("source_file",)
    date_hierarchy = "fecha_hora"
    ordering = ("-fecha_hora",)
