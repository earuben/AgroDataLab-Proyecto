from django.core.management.base import BaseCommand

from alerts.services import generate_alerts


class Command(BaseCommand):
    help = "Genera alertas explicables a partir de las lecturas EnviroPro importadas."

    def handle(self, *args, **options):
        total = generate_alerts()
        self.stdout.write(self.style.SUCCESS(f"Alertas generadas: {total}."))
