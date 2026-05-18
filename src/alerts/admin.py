from django.contrib import admin

from .models import Alert, Recommendation


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "fecha",
        "tipo",
        "nivel",
        "estado_manual",
        "variable_afectada",
        "valor_detectado",
    )
    list_filter = ("tipo", "nivel", "estado_manual")
    search_fields = ("descripcion", "recomendacion_texto", "regla", "observaciones")
    date_hierarchy = "fecha"
    ordering = ("-fecha",)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("titulo", "prioridad", "estado", "creada_por", "actualizada_en")
    list_filter = ("prioridad", "estado")
    search_fields = ("titulo", "descripcion")
    autocomplete_fields = ("alerta_relacionada", "creada_por")
    ordering = ("-actualizada_en",)
