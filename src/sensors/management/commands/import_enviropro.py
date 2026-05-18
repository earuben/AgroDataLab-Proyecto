import csv
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from sensors.models import EnviroProRecord


HUMIDITY_FIELDS = [f"hum_s{i}_media" for i in range(1, 9)]
TEMP_MEAN_FIELDS = [f"temp_s{i}_media" for i in range(1, 9)]
TEMP_MAX_FIELDS = [f"temp_s{i}_max" for i in range(1, 9)]
TEMP_MIN_FIELDS = [f"temp_s{i}_min" for i in range(1, 9)]
RAW_NUMERIC_FIELDS = [
    *HUMIDITY_FIELDS,
    *TEMP_MEAN_FIELDS,
    *TEMP_MAX_FIELDS,
    *TEMP_MIN_FIELDS,
]
REQUIRED_COLUMNS = {"fecha_hora", "bateria_mv", "panel_solar_mv"}
DEFAULT_CSV_PATH = (
    settings.PROJECT_ROOT / "data" / "processed" / "enviropro_completo_2024_2026.csv"
)


def parse_float(value):
    if value in {None, ""}:
        return None
    return float(str(value).replace(",", "."))


def parse_int(value):
    number = parse_float(value)
    if number is None:
        return None
    return int(round(number))


def parse_datetime(value):
    naive = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return timezone.make_aware(naive, timezone.get_current_timezone())


def average(values):
    clean_values = [value for value in values if value is not None]
    if not clean_values:
        return None
    return sum(clean_values) / len(clean_values)


class Command(BaseCommand):
    help = "Importa el CSV principal de lecturas EnviroPro sin duplicar fechas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=Path,
            default=DEFAULT_CSV_PATH,
            help="Ruta al CSV EnviroPro. Por defecto usa data/processed/enviropro_completo_2024_2026.csv.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Numero de filas entre mensajes de progreso.",
        )

    def handle(self, *args, **options):
        csv_path = options["path"]
        batch_size = options["batch_size"]

        if not csv_path.exists():
            raise CommandError(f"No existe el CSV: {csv_path}")

        processed = 0
        skipped = 0
        records = []
        update_fields = [
            field.name
            for field in EnviroProRecord._meta.fields
            if field.name not in {"id", "fecha_hora"}
        ]

        with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            if not reader.fieldnames:
                raise CommandError("El CSV no contiene cabecera.")

            missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise CommandError(f"Faltan columnas obligatorias: {missing}")

            for row_number, row in enumerate(reader, start=2):
                try:
                    fecha_hora = parse_datetime(row["fecha_hora"])
                    data = self.build_record_data(row)
                except (ValueError, TypeError) as exc:
                    skipped += 1
                    self.stderr.write(f"Fila {row_number} omitida: {exc}")
                    continue

                records.append(EnviroProRecord(fecha_hora=fecha_hora, **data))
                processed += 1

                if len(records) >= batch_size:
                    self.upsert_records(records, update_fields)
                    records = []
                    self.stdout.write(f"Procesadas {processed + skipped} filas...")

            if records:
                self.upsert_records(records, update_fields)

        self.stdout.write(
            self.style.SUCCESS(
                f"Importacion finalizada. Filas validas procesadas: {processed}. Omitidas: {skipped}."
            )
        )

    def upsert_records(self, records, update_fields):
        EnviroProRecord.objects.bulk_create(
            records,
            batch_size=len(records),
            update_conflicts=True,
            update_fields=update_fields,
            unique_fields=["fecha_hora"],
        )

    def build_record_data(self, row):
        data = {field: parse_float(row.get(field)) for field in RAW_NUMERIC_FIELDS}
        data["bateria_mv"] = parse_int(row.get("bateria_mv"))
        data["panel_solar_mv"] = parse_int(row.get("panel_solar_mv"))
        data["bateria_v"] = (
            data["bateria_mv"] / 1000 if data["bateria_mv"] is not None else None
        )
        data["panel_solar_v"] = (
            data["panel_solar_mv"] / 1000 if data["panel_solar_mv"] is not None else None
        )
        data["source_file"] = row.get("source_file", "")[:255]

        humidity_values = [data[field] for field in HUMIDITY_FIELDS]
        temp_mean_values = [data[field] for field in TEMP_MEAN_FIELDS]
        temp_min_values = [data[field] for field in TEMP_MIN_FIELDS]
        temp_max_values = [data[field] for field in TEMP_MAX_FIELDS]

        data["humedad_media"] = average(humidity_values)
        data["humedad_minima"] = min(
            [value for value in humidity_values if value is not None],
            default=None,
        )
        data["humedad_maxima"] = max(
            [value for value in humidity_values if value is not None],
            default=None,
        )
        data["temperatura_media"] = average(temp_mean_values)
        data["temperatura_minima"] = min(
            [value for value in temp_min_values if value is not None],
            default=None,
        )
        data["temperatura_maxima"] = max(
            [value for value in temp_max_values if value is not None],
            default=None,
        )
        return data
