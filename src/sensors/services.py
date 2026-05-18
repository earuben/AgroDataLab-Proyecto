from django.db.models import Avg, Count, Max, Min

from .models import EnviroProRecord


HUMIDITY_FIELDS = [f"hum_s{i}_media" for i in range(1, 9)]
TEMP_MEAN_FIELDS = [f"temp_s{i}_media" for i in range(1, 9)]


def get_record_summary():
    return EnviroProRecord.objects.aggregate(
        total=Count("id"),
        first_reading=Min("fecha_hora"),
        last_reading=Max("fecha_hora"),
        humidity_avg=Avg("humedad_media"),
        humidity_min=Min("humedad_minima"),
        humidity_max=Max("humedad_maxima"),
        temperature_avg=Avg("temperatura_media"),
        temperature_min=Min("temperatura_minima"),
        temperature_max=Max("temperatura_maxima"),
        battery_avg=Avg("bateria_v"),
        battery_min=Min("bateria_v"),
        solar_avg=Avg("panel_solar_v"),
        solar_max=Max("panel_solar_v"),
    )


def get_latest_records(limit=8):
    return EnviroProRecord.objects.order_by("-fecha_hora")[:limit]


def get_dashboard_snapshot():
    summary = get_record_summary()
    timeline_records = list(
        EnviroProRecord.objects.order_by("-fecha_hora")[:72]
    )
    timeline_records.reverse()
    return {
        "summary": summary,
        "latest_records": get_latest_records(6),
        "timeline": build_timeline_series(timeline_records),
        "humidity_sensor_bars": build_sensor_bars(HUMIDITY_FIELDS, "Humedad"),
        "temperature_sensor_bars": build_sensor_bars(TEMP_MEAN_FIELDS, "Temp."),
        "last_record": timeline_records[-1] if timeline_records else None,
    }


def build_timeline_series(records):
    series = {
        "humidity": [record.humedad_media for record in records],
        "temperature": [record.temperatura_media for record in records],
        "battery": [record.bateria_v for record in records],
        "solar": [record.panel_solar_v for record in records],
    }

    return {
        "labels": {
            "start": records[0].fecha_hora if records else None,
            "end": records[-1].fecha_hora if records else None,
        },
        "humidity_points": build_polyline(series["humidity"]),
        "temperature_points": build_polyline(series["temperature"]),
        "battery_points": build_polyline(series["battery"]),
        "solar_points": build_polyline(series["solar"]),
        "stats": {
            "humidity": build_series_stats(series["humidity"], "%"),
            "temperature": build_series_stats(series["temperature"], " C"),
            "battery": build_series_stats(series["battery"], " V", decimals=2),
            "solar": build_series_stats(series["solar"], " V", decimals=2),
        },
    }


def build_series_stats(values, suffix, decimals=1):
    clean_values = [value for value in values if value is not None]
    if not clean_values:
        return {"min": "Pendiente", "last": "Pendiente", "max": "Pendiente"}

    last_value = next((value for value in reversed(values) if value is not None), None)
    return {
        "min": f"{min(clean_values):.{decimals}f}{suffix}",
        "last": f"{last_value:.{decimals}f}{suffix}",
        "max": f"{max(clean_values):.{decimals}f}{suffix}",
    }


def build_polyline(values):
    clean_values = [value for value in values if value is not None]
    if not clean_values:
        return ""

    min_value = min(clean_values)
    max_value = max(clean_values)
    span = max(max_value - min_value, 0.0001)
    points = []
    total = max(len(values) - 1, 1)

    for index, value in enumerate(values):
        if value is None:
            continue
        x = (index / total) * 100
        y = 90 - ((value - min_value) / span) * 75
        points.append(f"{x:.2f},{y:.2f}")
    return " ".join(points)


def build_sensor_bars(fields, label_prefix):
    averages = EnviroProRecord.objects.aggregate(
        **{field: Avg(field) for field in fields}
    )
    max_value = max(
        [value for value in averages.values() if value is not None],
        default=1,
    )
    bars = []
    for index, field in enumerate(fields, start=1):
        value = averages[field]
        width = 0 if value is None else max(4, (value / max_value) * 100)
        bars.append(
            {
                "label": f"{label_prefix} S{index}",
                "value": value,
                "width": width,
            }
        )
    return bars
