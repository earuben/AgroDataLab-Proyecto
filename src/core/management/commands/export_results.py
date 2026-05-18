import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from alerts.models import Alert, Recommendation
from sensors.services import get_record_summary


class Command(BaseCommand):
    help = "Exporta alertas, recomendaciones y resumen de indicadores a CSV."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default="src/exports")

    def handle(self, *args, **options):
        output_dir = Path(settings.PROJECT_ROOT) / options["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)

        self.export_alerts(output_dir / "alertas.csv")
        self.export_recommendations(output_dir / "recomendaciones.csv")
        self.export_summary(output_dir / "resumen_indicadores.csv")

        self.stdout.write(self.style.SUCCESS(f"Resultados exportados en {output_dir}"))

    def export_alerts(self, path):
        rows = Alert.objects.select_related("record").order_by("fecha", "tipo")
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "fecha",
                    "tipo",
                    "nivel",
                    "variable_afectada",
                    "valor_detectado",
                    "descripcion",
                    "recomendacion_texto",
                    "regla",
                    "estado_manual",
                    "observaciones",
                ]
            )
            for alert in rows:
                writer.writerow(
                    [
                        alert.fecha.isoformat(),
                        alert.tipo,
                        alert.nivel,
                        alert.variable_afectada,
                        alert.valor_detectado,
                        alert.descripcion,
                        alert.recomendacion_texto,
                        alert.regla,
                        alert.estado_manual,
                        alert.observaciones,
                    ]
                )

    def export_recommendations(self, path):
        rows = Recommendation.objects.select_related("alerta_relacionada", "creada_por").order_by(
            "creada_en"
        )
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "titulo",
                    "descripcion",
                    "prioridad",
                    "estado",
                    "alerta_relacionada_id",
                    "alerta_tipo",
                    "creada_por",
                    "creada_en",
                    "actualizada_en",
                ]
            )
            for recommendation in rows:
                alert = recommendation.alerta_relacionada
                writer.writerow(
                    [
                        recommendation.titulo,
                        recommendation.descripcion,
                        recommendation.prioridad,
                        recommendation.estado,
                        alert.id if alert else "",
                        alert.tipo if alert else "",
                        recommendation.creada_por.username if recommendation.creada_por else "",
                        recommendation.creada_en.isoformat(),
                        recommendation.actualizada_en.isoformat(),
                    ]
                )

    def export_summary(self, path):
        summary = get_record_summary()
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["indicador", "valor"])
            for key, value in summary.items():
                writer.writerow([key, value.isoformat() if hasattr(value, "isoformat") else value])
            writer.writerow(["total_alertas", Alert.objects.count()])
            writer.writerow(["total_recomendaciones", Recommendation.objects.count()])
