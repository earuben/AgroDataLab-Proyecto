import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sensors.models import EnviroProRecord


FEATURES = [
    "humedad_media",
    "humedad_minima",
    "humedad_maxima",
    "humedad_delta",
    "humedad_media_rolling_6h",
    "temperatura_media",
    "temperatura_minima",
    "temperatura_maxima",
    "bateria_v",
    "panel_solar_v",
    "hora",
    "dia_semana",
]


class Command(BaseCommand):
    help = "Entrena un clasificador para predecir sequedad relativa en las proximas 24 horas."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default="src/ml/artifacts")
        parser.add_argument("--dryness-threshold", type=float, default=14.0)
        parser.add_argument("--test-size", type=float, default=0.25)

    def handle(self, *args, **options):
        df = self.load_dataframe()
        if len(df) < 100:
            raise CommandError("No hay suficientes registros para entrenar un modelo defendible.")

        threshold = options["dryness_threshold"]
        df = self.prepare_features(df, threshold)
        df = df.dropna(subset=FEATURES + ["target_dryness_24h"]).reset_index(drop=True)
        if df["target_dryness_24h"].nunique() < 2:
            raise CommandError("La variable objetivo solo tiene una clase; no se puede evaluar el clasificador.")

        split_index = int(len(df) * (1 - options["test_size"]))
        train = df.iloc[:split_index]
        test = df.iloc[split_index:]

        model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
                ),
            ]
        )
        model.fit(train[FEATURES], train["target_dryness_24h"])
        predictions = model.predict(test[FEATURES])

        metrics = {
            "target": f"Sequedad relativa en las proximas 24 horas: humedad_media < {threshold}",
            "features": FEATURES,
            "records_used": int(len(df)),
            "train_records": int(len(train)),
            "test_records": int(len(test)),
            "positive_rate_train": float(train["target_dryness_24h"].mean()),
            "positive_rate_test": float(test["target_dryness_24h"].mean()),
            "accuracy": float(accuracy_score(test["target_dryness_24h"], predictions)),
            "precision": float(precision_score(test["target_dryness_24h"], predictions, zero_division=0)),
            "recall": float(recall_score(test["target_dryness_24h"], predictions, zero_division=0)),
            "f1": float(f1_score(test["target_dryness_24h"], predictions, zero_division=0)),
            "confusion_matrix": confusion_matrix(test["target_dryness_24h"], predictions).tolist(),
            "interpretation": {
                "true_negative": "No predice alerta y no aparece sequedad en la ventana futura.",
                "false_positive": "Predice alerta pero no aparece sequedad; es una falsa alarma.",
                "false_negative": "No predice alerta pero aparece sequedad; es una alerta no detectada.",
                "true_positive": "Predice alerta y aparece sequedad en la ventana futura.",
                "limitations": "Modelo sencillo, dependiente del historico disponible y de reglas de sequedad definidas para el proyecto.",
            },
        }

        output_dir = Path(settings.PROJECT_ROOT) / options["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, output_dir / "dryness_classifier.joblib")
        (output_dir / "dryness_metrics.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        self.stdout.write(self.style.SUCCESS(f"Modelo guardado en {output_dir / 'dryness_classifier.joblib'}"))
        self.stdout.write(self.style.SUCCESS(f"Metricas guardadas en {output_dir / 'dryness_metrics.json'}"))
        self.stdout.write(
            "accuracy={accuracy:.3f} precision={precision:.3f} recall={recall:.3f} f1={f1:.3f}".format(
                **metrics
            )
        )

    def load_dataframe(self):
        rows = EnviroProRecord.objects.order_by("fecha_hora").values(
            "fecha_hora",
            "humedad_media",
            "humedad_minima",
            "humedad_maxima",
            "temperatura_media",
            "temperatura_minima",
            "temperatura_maxima",
            "bateria_v",
            "panel_solar_v",
        )
        return pd.DataFrame.from_records(rows)

    def prepare_features(self, df, threshold):
        df = df.sort_values("fecha_hora").reset_index(drop=True)
        df["hora"] = df["fecha_hora"].dt.hour
        df["dia_semana"] = df["fecha_hora"].dt.dayofweek
        df["humedad_delta"] = df["humedad_media"].diff()
        df["humedad_media_rolling_6h"] = (
            df.set_index("fecha_hora")["humedad_media"].rolling("6h", min_periods=1).mean().values
        )
        df["target_dryness_24h"] = self.future_dryness_target(
            df["fecha_hora"].to_numpy(),
            df["humedad_media"].to_numpy(),
            threshold,
        )
        return df

    def future_dryness_target(self, timestamps, humidity, threshold):
        targets = np.zeros(len(timestamps), dtype=int)
        for index, timestamp in enumerate(timestamps):
            start = np.searchsorted(timestamps, timestamp, side="right")
            end = np.searchsorted(timestamps, timestamp + np.timedelta64(24, "h"), side="right")
            future_values = humidity[start:end]
            future_values = future_values[~pd.isna(future_values)]
            targets[index] = int(len(future_values) > 0 and np.min(future_values) < threshold)
        return targets
