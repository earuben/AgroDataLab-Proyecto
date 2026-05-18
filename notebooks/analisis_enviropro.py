"""Analisis reproducible del dataset EnviroPro.

Ejecutar desde la raiz del proyecto:
    python notebooks/analisis_enviropro.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "enviropro_completo_2024_2026.csv"
REPORT_DIR = ROOT / "reports"
FIGURES_DIR = REPORT_DIR / "figures"

HUMIDITY_FIELDS = [f"hum_s{i}_media" for i in range(1, 9)]
TEMP_MEAN_FIELDS = [f"temp_s{i}_media" for i in range(1, 9)]
TEMP_MAX_FIELDS = [f"temp_s{i}_max" for i in range(1, 9)]
TEMP_MIN_FIELDS = [f"temp_s{i}_min" for i in range(1, 9)]
ENERGY_FIELDS = ["bateria_mv", "panel_solar_mv"]


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    numeric_cols = [c for c in df.columns if c != "source_file"]
    for column in numeric_cols:
        if column != "fecha_hora":
            df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.sort_values("fecha_hora").reset_index(drop=True)
    df["humedad_media"] = df[HUMIDITY_FIELDS].mean(axis=1)
    df["humedad_minima"] = df[HUMIDITY_FIELDS].min(axis=1)
    df["humedad_maxima"] = df[HUMIDITY_FIELDS].max(axis=1)
    df["temperatura_media"] = df[TEMP_MEAN_FIELDS].mean(axis=1)
    df["temperatura_minima"] = df[TEMP_MIN_FIELDS].min(axis=1)
    df["temperatura_maxima"] = df[TEMP_MAX_FIELDS].max(axis=1)
    df["bateria_v"] = df["bateria_mv"] / 1000
    df["panel_solar_v"] = df["panel_solar_mv"] / 1000
    return df


def save_plot(name):
    path = FIGURES_DIR / f"{name}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()
    return path


def line_plot(df, y, title, ylabel, name):
    plt.figure(figsize=(11, 4))
    plt.plot(df["fecha_hora"], df[y], linewidth=1)
    plt.title(title)
    plt.xlabel("Fecha")
    plt.ylabel(ylabel)
    return save_plot(name)


def bar_plot(series, title, ylabel, name):
    plt.figure(figsize=(9, 4))
    series.plot(kind="bar")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel("Sensor")
    return save_plot(name)


def build_quality_summary(df):
    duplicated_dates = int(df["fecha_hora"].duplicated().sum())
    duplicated_rows = int(df.duplicated().sum())
    gaps = df["fecha_hora"].diff().dropna()
    usual_frequency = gaps.mode().iloc[0] if not gaps.mode().empty else pd.NaT
    long_gaps = gaps[gaps > pd.Timedelta(hours=2)]
    nulls_by_sensor = df[HUMIDITY_FIELDS + TEMP_MEAN_FIELDS].isna().sum()
    stuck = {}
    for field in HUMIDITY_FIELDS:
        rounded = df[field].round(2)
        repeated = rounded.eq(rounded.shift()).astype(int)
        stuck[field] = int((repeated.rolling(8).sum() >= 7).sum())

    impossible = {
        "humedad_menor_0": int((df[HUMIDITY_FIELDS] < 0).sum().sum()),
        "humedad_mayor_100": int((df[HUMIDITY_FIELDS] > 100).sum().sum()),
        "temperatura_menor_-20": int((df[TEMP_MEAN_FIELDS] < -20).sum().sum()),
        "temperatura_mayor_60": int((df[TEMP_MEAN_FIELDS] > 60).sum().sum()),
        "bateria_no_positiva": int((df["bateria_mv"] <= 0).sum()),
        "panel_no_positivo": int((df["panel_solar_mv"] <= 0).sum()),
    }

    temp_incoherent = int(
        ((df["temperatura_maxima"] - df["temperatura_minima"]) > 18).sum()
    )
    energy_failures = int(((df["bateria_v"] < 6.2) | (df["panel_solar_v"] < 1.0)).sum())

    return {
        "duplicated_dates": duplicated_dates,
        "duplicated_rows": duplicated_rows,
        "usual_frequency": usual_frequency,
        "long_gaps": int(long_gaps.count()),
        "max_gap": long_gaps.max() if not long_gaps.empty else pd.Timedelta(0),
        "nulls_by_sensor": nulls_by_sensor,
        "stuck": stuck,
        "impossible": impossible,
        "temp_incoherent": temp_incoherent,
        "energy_failures": energy_failures,
    }


def generate_figures(df):
    weekly = df.set_index("fecha_hora").resample("W").mean(numeric_only=True)
    daily_alerts = pd.DataFrame(
        {
            "fecha": df["fecha_hora"].dt.date,
            "sequedad": df["humedad_media"] < 14,
            "energia": (df["bateria_v"] < 6.2) | (df["panel_solar_v"] < 1.0),
            "temperatura": df["temperatura_maxima"] > 32,
        }
    )
    daily_alerts = daily_alerts.groupby("fecha").sum(numeric_only=True)

    figures = {}
    figures["01_humedad_media_temporal"] = line_plot(
        df, "humedad_media", "Linea temporal de humedad media", "Humedad (%)", "01_humedad_media_temporal"
    )
    figures["02_temperatura_media_temporal"] = line_plot(
        df, "temperatura_media", "Linea temporal de temperatura media", "Temperatura (C)", "02_temperatura_media_temporal"
    )
    figures["03_bateria_temporal"] = line_plot(
        df, "bateria_v", "Linea temporal de bateria", "Bateria (V)", "03_bateria_temporal"
    )
    figures["04_panel_solar_temporal"] = line_plot(
        df, "panel_solar_v", "Linea temporal del panel solar", "Panel solar (V)", "04_panel_solar_temporal"
    )
    figures["05_humedad_por_sensor"] = bar_plot(
        df[HUMIDITY_FIELDS].mean(), "Comparacion de humedad por sensor", "Humedad media (%)", "05_humedad_por_sensor"
    )
    figures["06_temperatura_por_sensor"] = bar_plot(
        df[TEMP_MEAN_FIELDS].mean(), "Comparacion de temperatura promedio por sensor", "Temperatura media (C)", "06_temperatura_por_sensor"
    )
    figures["07_humedad_semanal"] = line_plot(
        weekly.reset_index(), "humedad_media", "Evolucion semanal de humedad", "Humedad (%)", "07_humedad_semanal"
    )
    figures["08_temperatura_semanal"] = line_plot(
        weekly.reset_index(), "temperatura_media", "Evolucion semanal de temperatura", "Temperatura (C)", "08_temperatura_semanal"
    )

    plt.figure(figsize=(5, 4))
    corr = df[["humedad_media", "temperatura_media", "bateria_v", "panel_solar_v"]].corr()
    plt.imshow(corr, cmap="viridis", vmin=-1, vmax=1)
    plt.xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
    plt.yticks(range(len(corr)), corr.columns)
    plt.colorbar(label="Correlacion")
    plt.title("Correlacion entre humedad y temperatura")
    figures["09_correlacion_humedad_temperatura"] = save_plot("09_correlacion_humedad_temperatura")

    plt.figure(figsize=(7, 4))
    plt.scatter(df["humedad_media"], df["temperatura_media"], s=8, alpha=0.35)
    plt.title("Dispersion humedad media vs temperatura media")
    plt.xlabel("Humedad media (%)")
    plt.ylabel("Temperatura media (C)")
    figures["10_dispersion_humedad_temperatura"] = save_plot("10_dispersion_humedad_temperatura")

    plt.figure(figsize=(11, 4))
    daily_alerts.plot(ax=plt.gca(), linewidth=1)
    plt.title("Alertas detectadas por dia")
    plt.xlabel("Fecha")
    plt.ylabel("Numero de alertas")
    figures["11_alertas_por_dia"] = save_plot("11_alertas_por_dia")

    plt.figure(figsize=(10, 4))
    df[HUMIDITY_FIELDS + TEMP_MEAN_FIELDS].isna().sum().plot(kind="bar")
    plt.title("Valores nulos o problemas por sensor")
    plt.ylabel("Valores nulos")
    figures["12_nulos_por_sensor"] = save_plot("12_nulos_por_sensor")
    return figures


def write_report(df, quality, figures):
    report = []
    report.append("# Analisis EnviroPro\n")
    report.append("## Comprension inicial\n")
    report.append(f"- Archivo analizado: `{DATA_PATH.relative_to(ROOT)}`\n")
    report.append(f"- Numero de registros: {len(df):,}\n".replace(",", "."))
    report.append(f"- Numero de columnas originales: {len(pd.read_csv(DATA_PATH, nrows=1).columns)}\n")
    report.append(f"- Primera lectura: {df['fecha_hora'].min()}\n")
    report.append(f"- Ultima lectura: {df['fecha_hora'].max()}\n")
    report.append("- La fecha/hora se interpreta con `pd.to_datetime`; el CSV ya usa punto decimal, no coma decimal.\n")
    report.append("- Humedad y temperatura se analizan por sensores S1-S8; bateria y panel solar vienen en mV y se convierten a V.\n")

    report.append("\n## Limpieza y calidad de datos\n")
    report.append(f"- Duplicados exactos: {quality['duplicated_rows']}\n")
    report.append(f"- Fechas duplicadas: {quality['duplicated_dates']}\n")
    report.append(f"- Frecuencia aproximada mas habitual: {quality['usual_frequency']}\n")
    report.append(f"- Huecos temporales mayores de 2 horas: {quality['long_gaps']} (maximo {quality['max_gap']})\n")
    report.append(f"- Temperaturas incoherentes por rango > 18 C: {quality['temp_incoherent']}\n")
    report.append(f"- Lecturas con posible fallo energetico: {quality['energy_failures']}\n")
    for key, value in quality["impossible"].items():
        report.append(f"- {key}: {value}\n")

    report.append("\n## Interpretacion de visualizaciones\n")
    interpretations = [
        ("01_humedad_media_temporal", "La humedad media permite localizar periodos secos y recuperaciones tras posibles aportes de agua."),
        ("02_temperatura_media_temporal", "La temperatura media muestra la estacionalidad esperada y ayuda a contextualizar la sequedad."),
        ("03_bateria_temporal", "La bateria en V permite detectar etapas de riesgo energetico del nodo."),
        ("04_panel_solar_temporal", "El panel solar presenta variabilidad diaria y sirve para revisar carga o sombras."),
        ("05_humedad_por_sensor", "La comparacion por sensor muestra diferencias por profundidad o ubicacion y sensores que conviene revisar."),
        ("06_temperatura_por_sensor", "La temperatura promedio por sensor ayuda a detectar sensores con comportamiento distinto."),
        ("07_humedad_semanal", "La serie semanal suaviza ruido horario y deja ver tendencias de humedad defendibles."),
        ("08_temperatura_semanal", "La temperatura semanal resume la evolucion termica sin depender de lecturas puntuales."),
        ("09_correlacion_humedad_temperatura", "La matriz resume relaciones lineales entre humedad, temperatura y energia."),
        ("10_dispersion_humedad_temperatura", "La dispersion permite ver si temperaturas altas coinciden con humedades bajas."),
        ("11_alertas_por_dia", "Las alertas por dia concentran los periodos que requieren revision prioritaria."),
        ("12_nulos_por_sensor", "Los nulos por sensor muestran ausencias y posibles problemas de calidad de datos."),
    ]
    for key, text in interpretations:
        report.append(f"- `{figures[key].relative_to(ROOT)}`: {text}\n")

    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "analisis_enviropro.md").write_text("".join(report), encoding="utf-8")


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    quality = build_quality_summary(df)
    figures = generate_figures(df)
    write_report(df, quality, figures)
    print(f"Analisis generado en {REPORT_DIR / 'analisis_enviropro.md'}")
    print(f"Figuras generadas en {FIGURES_DIR}")


if __name__ == "__main__":
    main()
