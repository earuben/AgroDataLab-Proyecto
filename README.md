# AgroDataLab EnviroPro

AgroDataLab Web es una aplicacion Django para analizar lecturas de sensores EnviroPro, generar alertas explicables, gestionar recomendaciones y entrenar un modelo sencillo de clasificacion para anticipar sequedad relativa.

## Integrantes

- Integrante 1: PENDIENTE
- Integrante 2: PENDIENTE

## Problema

El objetivo es transformar lecturas de humedad, temperatura y energia de sensores EnviroPro en informacion util para seguimiento agricola. La aplicacion no sustituye criterio tecnico: prioriza revision de datos, alertas y recomendaciones prudentes.

## Dataset

Archivo principal:

```text
data/processed/enviropro_completo_2024_2026.csv
```

Variables analizadas:

- Fecha y hora de lectura.
- Humedad media por sensores S1-S8.
- Temperatura media, minima y maxima por sensores S1-S8.
- Bateria y panel solar en mV, convertidos tambien a V.
- Indicadores derivados: medias generales, minimos, maximos, huecos temporales y alertas.

IFAPA-RIA queda fuera de Django y solo se considera ampliacion opcional en informe o notebook.

## Instalacion local

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe src\manage.py migrate
```

## Comandos principales

Ejecutar desde `src/`:

```powershell
..\.venv\Scripts\python.exe manage.py createsuperuser
..\.venv\Scripts\python.exe manage.py import_enviropro
..\.venv\Scripts\python.exe manage.py generate_alerts
..\.venv\Scripts\python.exe manage.py suggest_recommendations --limit 25
..\.venv\Scripts\python.exe manage.py train_dryness_model
..\.venv\Scripts\python.exe manage.py export_results
..\.venv\Scripts\python.exe manage.py runserver
```

Analisis reproducible desde la raiz:

```powershell
.\.venv\Scripts\python.exe notebooks\analisis_enviropro.py
```

Tambien se incluye notebook ejecutable:

```text
notebooks/analisis_enviropro.ipynb
```

Salidas generadas:

- `reports/analisis_enviropro.md`
- `reports/figures/`
- `src/ml/artifacts/dryness_classifier.joblib`
- `src/ml/artifacts/dryness_metrics.json`
- `src/exports/alertas.csv`
- `src/exports/recomendaciones.csv`
- `src/exports/resumen_indicadores.csv`

## Web Django

Paginas incluidas:

- Inicio.
- Login, logout y registro con autenticacion oficial de Django.
- Usuarios.
- Dashboard privado.
- Alertas.
- Importacion.
- Alertas con revision manual, estado pendiente/revisada/descartada y observaciones por lectura o dia concreto.
- Recomendaciones con CRUD, estado pendiente/en revision/revisada/descartada y asociacion a alerta.
- Acerca del proyecto.

Usuario de prueba para entrega: PENDIENTE. No incluir contrasenas personales en este README.

## Alertas

Reglas implementadas:

- Sequedad relativa.
- Humedad baja en sensor.
- Subida brusca de humedad.
- Caida brusca de humedad.
- Temperatura alta.
- Temperatura incoherente.
- Bateria baja.
- Panel solar bajo en horario diurno.
- Sensor posiblemente bloqueado.
- Hueco temporal.

Las reglas son deterministas y explicables. Las recomendaciones generadas son prudentes y piden contrastar con lecturas cercanas o revision tecnica.

Cada alerta puede revisarse manualmente desde la web para anotar observaciones o descartar falsos positivos. Si se regenera el conjunto de alertas con el comando `generate_alerts`, se recalculan desde las lecturas disponibles.

## Modelo predictivo

Comando:

```powershell
..\.venv\Scripts\python.exe manage.py train_dryness_model
```

Objetivo: predecir si aparecera sequedad relativa en las proximas 24 horas (`humedad_media < 14`).

Enfoque:

- Clasificacion con `LogisticRegression`.
- Separacion cronologica train/test.
- Features de humedad, variacion de humedad, temperatura, bateria, panel solar, hora, dia de semana y media movil de humedad.
- Metricas guardadas: accuracy, precision, recall, F1 y matriz de confusion.

## Despliegue en PythonAnywhere

1. Subir el repositorio a PythonAnywhere.
2. Crear entorno virtual e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Crear `.env` basado en `.env.example`:

```text
DJANGO_SECRET_KEY=valor-seguro
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tuusuario.pythonanywhere.com
```

4. Configurar la web app:

```text
Source code: /home/tuusuario/agrodatalab_minimo
Working directory: /home/tuusuario/agrodatalab_minimo/src
WSGI: config.wsgi
Static files URL: /static/
Static files path: /home/tuusuario/agrodatalab_minimo/src/staticfiles
```

5. Ejecutar:

```bash
cd src
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py import_enviropro
python manage.py generate_alerts
```

URL publica: PENDIENTE.

## Video

Enlace al video explicativo: PENDIENTE.

## Conclusiones

El proyecto permite importar datos reales EnviroPro, visualizar indicadores principales, detectar problemas de humedad, temperatura, energia y calidad de datos, y gestionar recomendaciones asociadas a alertas. El modelo predictivo aporta una primera aproximacion defendible a la anticipacion de sequedad relativa.

## Limitaciones

- Las alertas dependen de umbrales explicables, no de validacion agronomica externa.
- El modelo usa el historico disponible y debe revisarse si cambia el comportamiento del cultivo, sensores o frecuencia de datos.
- La URL publica, video, integrantes y credenciales de prueba quedan como datos manuales de entrega.

## Mejoras futuras

- Ajustar umbrales con criterio tecnico.
- Comparar modelos de clasificacion adicionales si se justifica.
- Anadir validacion de campo para confirmar falsas alarmas y alertas no detectadas.
