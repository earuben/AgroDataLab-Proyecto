from datetime import timedelta

from django.db.models import Case, Count, IntegerField, When
from django.utils import timezone

from sensors.models import EnviroProRecord

from .models import Alert, Recommendation


LOW_HUMIDITY_THRESHOLD = 14.0
CRITICAL_HUMIDITY_THRESHOLD = 10.0
LOW_SENSOR_HUMIDITY_THRESHOLD = 8.0
HIGH_TEMPERATURE_THRESHOLD = 32.0
INCOHERENT_TEMP_SPAN_THRESHOLD = 18.0
LOW_BATTERY_V_THRESHOLD = 6.2
LOW_SOLAR_PANEL_V_THRESHOLD = 1.0
DAYLIGHT_START_HOUR = 10
DAYLIGHT_END_HOUR = 17
TIME_GAP_THRESHOLD = timedelta(hours=2)
HUMIDITY_JUMP_THRESHOLD = 8.0
STUCK_SENSOR_TOLERANCE = 0.05
STUCK_SENSOR_REPEAT_COUNT = 8
HUMIDITY_SENSOR_FIELDS = [f"hum_s{i}_media" for i in range(1, 9)]


def get_alert_summary():
    total = Alert.objects.count()
    by_level = {
        item["nivel"]: item["total"]
        for item in Alert.objects.values("nivel").annotate(total=Count("id"))
    }
    by_type = []
    for item in Alert.objects.values("tipo").annotate(total=Count("id")).order_by("-total"):
        by_type.append(
            {
                "tipo": item["tipo"],
                "label": Alert.AlertType(item["tipo"]).label,
                "total": item["total"],
            }
        )
    dryness_count = Alert.objects.filter(tipo=Alert.AlertType.RELATIVE_DRYNESS).count()
    energy_count = Alert.objects.filter(
        tipo__in=[Alert.AlertType.LOW_BATTERY, Alert.AlertType.LOW_SOLAR_PANEL]
    ).count()
    incoherent_temperature_count = Alert.objects.filter(
        tipo=Alert.AlertType.INCOHERENT_TEMPERATURE
    ).count()
    return {
        "total": total,
        "critical": by_level.get(Alert.Level.CRITICAL, 0),
        "warning": by_level.get(Alert.Level.WARNING, 0),
        "info": by_level.get(Alert.Level.INFO, 0),
        "dryness_count": dryness_count,
        "energy_count": energy_count,
        "incoherent_temperature_count": incoherent_temperature_count,
        "by_type": by_type,
    }


def get_recommendation_summary():
    total = Recommendation.objects.count()
    pending = Recommendation.objects.filter(estado=Recommendation.Status.PENDING).count()
    in_progress = Recommendation.objects.filter(
        estado=Recommendation.Status.IN_PROGRESS
    ).count()
    done = Recommendation.objects.filter(estado=Recommendation.Status.DONE).count()
    urgent = Recommendation.objects.filter(
        prioridad=Recommendation.Priority.URGENT
    ).count()
    return {
        "total": total,
        "open": pending + in_progress,
        "pending": pending,
        "in_progress": in_progress,
        "done": done,
        "urgent": urgent,
    }


def get_recent_alerts(limit=6):
    return order_alerts_by_priority(Alert.objects.select_related("record"))[:limit]


def get_recent_recommendations(limit=6):
    return Recommendation.objects.select_related(
        "alerta_relacionada", "creada_por"
    ).order_by("-actualizada_en", "-creada_en")[:limit]


def create_recommendations_from_alerts(limit=25, user=None):
    alerts = order_alerts_by_priority(
        Alert.objects.exclude(recommendations__isnull=False)
        .filter(nivel__in=[Alert.Level.CRITICAL, Alert.Level.WARNING])
    )[:limit]
    recommendations = []
    for alert in alerts:
        recommendations.append(
            Recommendation(
                titulo=build_recommendation_title(alert),
                descripcion=build_recommendation_description(alert),
                alerta_relacionada=alert,
                prioridad=map_alert_priority(alert),
                estado=Recommendation.Status.PENDING,
                creada_por=user,
            )
        )
    Recommendation.objects.bulk_create(recommendations, batch_size=200)
    return len(recommendations)


def build_recommendation_title(alert):
    return f"Revisar {alert.get_tipo_display().lower()} del {alert.fecha:%d/%m/%Y %H:%M}"


def build_recommendation_description(alert):
    return (
        f"Alerta detectada: {alert.descripcion}\n\n"
        f"Accion recomendada con prudencia: {alert.recomendacion_texto}\n\n"
        "Antes de ejecutar una actuacion en campo, contrastar con lecturas cercanas, "
        "estado del sensor y criterio tecnico."
    )


def map_alert_priority(alert):
    if alert.nivel == Alert.Level.CRITICAL:
        return Recommendation.Priority.URGENT
    if alert.tipo in {
        Alert.AlertType.RELATIVE_DRYNESS,
        Alert.AlertType.LOW_SENSOR_HUMIDITY,
        Alert.AlertType.LOW_BATTERY,
    }:
        return Recommendation.Priority.HIGH
    return Recommendation.Priority.MEDIUM


def order_alerts_by_priority(queryset):
    return queryset.annotate(
        priority_rank=Case(
            When(nivel=Alert.Level.CRITICAL, then=0),
            When(nivel=Alert.Level.WARNING, then=1),
            default=2,
            output_field=IntegerField(),
        )
    ).order_by("priority_rank", "-fecha")


def generate_alerts():
    Alert.objects.all().delete()

    alerts = []
    previous_record = None
    sensor_state = {}
    records = EnviroProRecord.objects.order_by("fecha_hora").iterator(chunk_size=1000)

    for record in records:
        alerts.extend(build_record_alerts(record, previous_record, sensor_state))
        previous_record = record

    Alert.objects.bulk_create(alerts, batch_size=1000, ignore_conflicts=True)
    return len(alerts)


def build_record_alerts(record, previous_record=None, sensor_state=None):
    alerts = []
    alerts.extend(build_humidity_alerts(record))
    alerts.extend(build_temperature_alerts(record))
    alerts.extend(build_energy_alerts(record))

    if previous_record is not None:
        gap = record.fecha_hora - previous_record.fecha_hora
        alerts.extend(build_humidity_change_alerts(record, previous_record, gap))
        if gap > TIME_GAP_THRESHOLD:
            alerts.append(
                make_alert(
                    record,
                    Alert.AlertType.TIME_GAP,
                    Alert.Level.INFO,
                    f"Hueco temporal de {gap} desde la lectura anterior.",
                    "fecha_hora",
                    gap.total_seconds() / 3600,
                    "Revisar si hubo parada de registro, perdida de comunicacion o fichero intermedio no importado.",
                    "gap_gt_2h",
                )
            )
    if sensor_state is not None:
        alerts.extend(build_stuck_sensor_alerts(record, sensor_state))
    return alerts


def build_humidity_alerts(record):
    alerts = []
    if record.humedad_media is not None and record.humedad_media < LOW_HUMIDITY_THRESHOLD:
        level = (
            Alert.Level.CRITICAL
            if record.humedad_media < CRITICAL_HUMIDITY_THRESHOLD
            else Alert.Level.WARNING
        )
        alerts.append(
            make_alert(
                record,
                Alert.AlertType.RELATIVE_DRYNESS,
                level,
                f"Humedad media baja: {record.humedad_media:.2f}%.",
                "humedad_media",
                record.humedad_media,
                "Contrastar con la tendencia reciente y revisar si conviene planificar riego o inspeccion de campo.",
                "humedad_media_lt_14",
            )
        )

    if record.humedad_minima is not None and record.humedad_minima < LOW_SENSOR_HUMIDITY_THRESHOLD:
        alerts.append(
            make_alert(
                record,
                Alert.AlertType.LOW_SENSOR_HUMIDITY,
                Alert.Level.WARNING,
                f"Al menos un sensor registra humedad muy baja: {record.humedad_minima:.2f}%.",
                "humedad_minima",
                record.humedad_minima,
                "Comprobar el sensor afectado y comparar con el resto de profundidades antes de tomar decisiones.",
                "humedad_minima_lt_8",
            )
        )
    return alerts


def build_humidity_change_alerts(record, previous_record, gap):
    alerts = []
    if gap > TIME_GAP_THRESHOLD:
        return alerts
    if record.humedad_media is None or previous_record.humedad_media is None:
        return alerts

    delta = record.humedad_media - previous_record.humedad_media
    if delta >= HUMIDITY_JUMP_THRESHOLD:
        alerts.append(
            make_alert(
                record,
                Alert.AlertType.HUMIDITY_SHARP_RISE,
                Alert.Level.INFO,
                f"Subida brusca de humedad media: +{delta:.2f} puntos desde la lectura anterior.",
                "humedad_media",
                delta,
                "Comprobar si coincide con riego, lluvia o recuperacion real antes de interpretarlo como cambio estable.",
                "humedad_media_rise_gte_8",
            )
        )
    elif delta <= -HUMIDITY_JUMP_THRESHOLD:
        alerts.append(
            make_alert(
                record,
                Alert.AlertType.HUMIDITY_SHARP_DROP,
                Alert.Level.WARNING,
                f"Caida brusca de humedad media: {delta:.2f} puntos desde la lectura anterior.",
                "humedad_media",
                delta,
                "Revisar tendencia posterior y descartar fallo puntual del sensor antes de decidir una actuacion.",
                "humedad_media_drop_lte_minus_8",
            )
        )
    return alerts


def build_stuck_sensor_alerts(record, sensor_state):
    alerts = []
    for field in HUMIDITY_SENSOR_FIELDS:
        value = getattr(record, field)
        state = sensor_state.get(field, {"last": None, "count": 0, "since": record.fecha_hora})
        if value is None:
            sensor_state[field] = {"last": None, "count": 0, "since": record.fecha_hora}
            continue

        last_value = state["last"]
        if last_value is not None and abs(value - last_value) <= STUCK_SENSOR_TOLERANCE:
            count = state["count"] + 1
            since = state["since"]
        else:
            count = 1
            since = record.fecha_hora

        sensor_state[field] = {"last": value, "count": count, "since": since}
        if count == STUCK_SENSOR_REPEAT_COUNT:
            sensor_label = field.replace("_media", "").upper()
            hours = (record.fecha_hora - since).total_seconds() / 3600
            alerts.append(
                make_alert(
                    record,
                    Alert.AlertType.STUCK_SENSOR,
                    Alert.Level.INFO,
                    f"{sensor_label} mantiene practicamente el mismo valor ({value:.2f}%) durante {count} lecturas consecutivas.",
                    field,
                    value,
                    f"Revisar si el sensor {sensor_label} esta bloqueado, desconectado o si realmente no hubo variacion en unas {hours:.1f} horas.",
                    f"{field}_stuck_8_reads",
                )
            )
    return alerts


def build_temperature_alerts(record):
    alerts = []
    if record.temperatura_maxima is not None and record.temperatura_maxima > HIGH_TEMPERATURE_THRESHOLD:
        alerts.append(
            make_alert(
                record,
                Alert.AlertType.HIGH_TEMPERATURE,
                Alert.Level.WARNING,
                f"Temperatura maxima alta: {record.temperatura_maxima:.2f} C.",
                "temperatura_maxima",
                record.temperatura_maxima,
                "Vigilar la evolucion termica y cruzarla con humedad antes de interpretar estres hidrico.",
                "temperatura_maxima_gt_32",
            )
        )

    if (
        record.temperatura_maxima is not None
        and record.temperatura_minima is not None
        and record.temperatura_maxima - record.temperatura_minima > INCOHERENT_TEMP_SPAN_THRESHOLD
    ):
        span = record.temperatura_maxima - record.temperatura_minima
        alerts.append(
            make_alert(
                record,
                Alert.AlertType.INCOHERENT_TEMPERATURE,
                Alert.Level.INFO,
                f"Diferencia amplia entre temperatura maxima y minima: {span:.2f} C.",
                "temperatura_rango",
                span,
                "Revisar si hay lectura puntual anomala o sensor con comportamiento distinto al resto.",
                "temperatura_rango_gt_18",
            )
        )
    return alerts


def build_energy_alerts(record):
    alerts = []
    if record.bateria_v is not None and record.bateria_v < LOW_BATTERY_V_THRESHOLD:
        alerts.append(
            make_alert(
                record,
                Alert.AlertType.LOW_BATTERY,
                Alert.Level.CRITICAL,
                f"Bateria baja: {record.bateria_v:.2f} V.",
                "bateria_v",
                record.bateria_v,
                "Programar revision energetica del nodo para evitar perdida de datos.",
                "bateria_v_lt_6_2",
            )
        )

    local_hour = timezone.localtime(record.fecha_hora).hour
    is_daylight_window = DAYLIGHT_START_HOUR <= local_hour <= DAYLIGHT_END_HOUR
    if (
        is_daylight_window
        and record.panel_solar_v is not None
        and record.panel_solar_v < LOW_SOLAR_PANEL_V_THRESHOLD
    ):
        alerts.append(
            make_alert(
                record,
                Alert.AlertType.LOW_SOLAR_PANEL,
                Alert.Level.WARNING,
                f"Panel solar bajo en horario diurno: {record.panel_solar_v:.2f} V.",
                "panel_solar_v",
                record.panel_solar_v,
                "Revisar orientacion, suciedad, sombra o posible desconexion del panel.",
                "panel_solar_v_lt_1_daytime",
            )
        )
    return alerts


def make_alert(record, alert_type, level, description, variable, value, recommendation, rule):
    return Alert(
        record=record,
        fecha=record.fecha_hora,
        tipo=alert_type,
        nivel=level,
        descripcion=description,
        variable_afectada=variable,
        valor_detectado=value,
        recomendacion_texto=recommendation,
        regla=rule,
    )
