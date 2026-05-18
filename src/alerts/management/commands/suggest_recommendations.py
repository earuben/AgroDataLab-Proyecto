from django.core.management.base import BaseCommand

from alerts.services import create_recommendations_from_alerts


class Command(BaseCommand):
    help = "Crea recomendaciones iniciales desde alertas criticas o de aviso sin recomendacion vinculada."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=25,
            help="Numero maximo de recomendaciones a crear.",
        )

    def handle(self, *args, **options):
        created = create_recommendations_from_alerts(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(f"Recomendaciones sugeridas creadas: {created}."))
