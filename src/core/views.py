from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib.auth.models import User

from alerts.services import (
    get_alert_summary,
    get_recent_alerts,
    get_recent_recommendations,
    get_recommendation_summary,
)
from alerts.models import Recommendation
from sensors.services import get_dashboard_snapshot


def format_number(value, decimals=1, suffix=""):
    if value is None:
        return "Pendiente"
    return f"{value:.{decimals}f}{suffix}"


def home(request):
    return render(request, "core/home.html")


@login_required
def about(request):
    return render(request, "core/about.html")


@login_required
def users(request):
    context = {
        "users_count": User.objects.count(),
        "active_users_count": User.objects.filter(is_active=True).count(),
        "staff_users_count": User.objects.filter(is_staff=True).count(),
        "current_user_recommendations": Recommendation.objects.filter(
            creada_por=request.user
        ).count(),
    }
    return render(request, "core/users.html", context)


@login_required
def dashboard(request):
    snapshot = get_dashboard_snapshot()
    summary = snapshot["summary"]
    alert_summary = get_alert_summary()
    recommendation_summary = get_recommendation_summary()
    context = {
        "sensor_cards": [
            {
                "label": "Registros cargados",
                "value": summary["total"] or 0,
                "hint": "Lecturas EnviroPro",
                "tone": "aqua",
            },
            {
                "label": "Humedad media",
                "value": format_number(summary["humidity_avg"], suffix="%"),
                "hint": f"Min {format_number(summary['humidity_min'], suffix='%')} / Max {format_number(summary['humidity_max'], suffix='%')}",
                "tone": "green",
            },
            {
                "label": "Temperatura",
                "value": format_number(summary["temperature_avg"], suffix=" C"),
                "hint": f"Min {format_number(summary['temperature_min'], suffix=' C')} / Max {format_number(summary['temperature_max'], suffix=' C')}",
                "tone": "amber",
            },
            {
                "label": "Bateria media",
                "value": format_number(summary["battery_avg"], decimals=2, suffix=" V"),
                "hint": f"Min {format_number(summary['battery_min'], decimals=2, suffix=' V')}",
                "tone": "blue",
            },
            {
                "label": "Panel solar medio",
                "value": format_number(summary["solar_avg"], decimals=2, suffix=" V"),
                "hint": f"Max {format_number(summary['solar_max'], decimals=2, suffix=' V')}",
                "tone": "amber",
            },
        ],
        "required_indicators": [
            ("Total de registros cargados", summary["total"] or 0),
            ("Primera lectura", summary["first_reading"]),
            ("Ultima lectura", summary["last_reading"]),
            ("Humedad media general", format_number(summary["humidity_avg"], suffix="%")),
            ("Temperatura media general", format_number(summary["temperature_avg"], suffix=" C")),
            ("Bateria media", format_number(summary["battery_avg"], decimals=2, suffix=" V")),
            ("Panel solar medio", format_number(summary["solar_avg"], decimals=2, suffix=" V")),
            ("Alertas de sequedad", alert_summary["dryness_count"]),
            ("Alertas energeticas", alert_summary["energy_count"]),
            ("Alertas de temperatura incoherente", alert_summary["incoherent_temperature_count"]),
        ],
        "latest_recommendation": Recommendation.objects.order_by("-creada_en").first(),
        "summary": summary,
        "alert_summary": alert_summary,
        "recommendation_summary": recommendation_summary,
        "recent_alerts": get_recent_alerts(),
        "recent_recommendations": get_recent_recommendations(),
        "latest_records": snapshot["latest_records"],
        "timeline": snapshot["timeline"],
        "humidity_sensor_bars": snapshot["humidity_sensor_bars"],
        "temperature_sensor_bars": snapshot["temperature_sensor_bars"],
        "last_record": snapshot["last_record"],
        "phase_items": [
            "Datos reales importados en SQLite",
            "Metricas generales conectadas al dashboard",
            "Alertas y recomendaciones integradas",
            "Proyecto listo para iniciar la fase predictiva",
        ],
    }
    return render(request, "core/dashboard.html", context)
