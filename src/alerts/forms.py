from django import forms

from .models import Alert, Recommendation


class AlertReviewForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ["estado_manual", "observaciones"]
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Anota la revision realizada, lectura de campo o motivo para descartar la alerta.",
                }
            ),
        }


class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = [
            "titulo",
            "descripcion",
            "alerta_relacionada",
            "prioridad",
            "estado",
        ]
        widgets = {
            "titulo": forms.TextInput(
                attrs={"placeholder": "Ej. Revisar zona con humedad baja persistente"}
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Describe una accion prudente, verificable y defendible.",
                }
            ),
        }
