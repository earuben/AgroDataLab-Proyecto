# Guía mínima para desarrollar AgroDataLab EnviroPro con Codex

## 1. Resumen del proyecto

Hay que crear una aplicación de análisis de datos y web con Django basada en sensores EnviroPro.
El proyecto se divide en:

1. Análisis de datos.
2. Sistema de alertas y recomendaciones.
3. Modelo predictivo sencillo.
4. Aplicación web Django.
5. Despliegue.
6. README y vídeo explicativo.

La ampliación IFAPA-RIA queda como extra opcional fuera de Django.

## 2. Dataset principal

Usar este archivo:

```text
data/processed/enviropro_completo_2024_2026.csv
```

Columnas esperadas:

- fecha_hora
- hum_s1_media
- hum_s2_media
- hum_s3_media
- temp_s1_media
- temp_s1_max
- temp_s1_min
- temp_s2_media
- temp_s2_max
- temp_s2_min
- temp_s3_media
- temp_s3_max
- temp_s3_min
- bateria_mv
- panel_solar_mv

No se debe depender de que haya exactamente las mismas fechas siempre. El código debe ser robusto.

## 3. Fase Django mínima

Crear un proyecto Django con apps recomendadas:

```text
config/          configuración principal
core/            inicio, layout, páginas generales
accounts/        login, logout, registro si se hace personalizado
sensors/         registros EnviroPro, importación y dashboard
alerts/          alertas y recomendaciones
ml/              entrenamiento y predicción
```

También se puede simplificar si conviene, pero debe quedar limpio.

## 4. Modelos recomendados

### EnviroProRecord

Campos orientativos:

- fecha_hora
- humedad_media
- humedad_minima
- humedad_maxima
- temperatura_media
- temperatura_maxima
- temperatura_minima
- bateria_mv
- bateria_v
- panel_solar_mv
- panel_solar_v
- observaciones

### Alert

Campos orientativos:

- fecha
- tipo
- nivel
- descripcion
- variable_afectada
- valor_detectado
- recomendacion_texto
- creada_en

### Recommendation

Campos orientativos:

- titulo
- descripcion
- alerta_relacionada
- prioridad
- estado
- creada_por
- creada_en
- actualizada_en

Debe existir CRUD de recomendaciones.

## 5. Login y seguridad

Usar el sistema oficial de Django:

- django.contrib.auth
- LoginView
- LogoutView
- decorators o mixins como LoginRequiredMixin
- CSRF activo
- password hashing estándar de Django

No crear autenticación manual guardando contraseñas en texto plano.

## 6. Dashboard mínimo

El dashboard debe mostrar:

- total de registros cargados
- fecha de primera lectura
- fecha de última lectura
- humedad media general
- temperatura media general
- batería media
- panel solar medio
- número de alertas de sequedad
- número de alertas energéticas
- número de alertas de temperatura incoherente
- última recomendación generada

También debe incluir gráficos de EnviroPro.

## 7. Visualizaciones mínimas

Crear al menos estas visualizaciones en análisis/notebook y algunas en la web:

1. Línea temporal de humedad media.
2. Línea temporal de temperatura media.
3. Línea temporal de batería.
4. Línea temporal del panel solar.
5. Comparación de humedad por sensor.
6. Comparación de temperatura por sensor.
7. Evolución diaria o semanal de humedad.
8. Evolución diaria o semanal de temperatura.
9. Correlación humedad-temperatura.
10. Alertas por día o semana.

## 8. Alertas mínimas

Crear reglas explicables para:

- sequedad relativa
- humedad muy baja en sensor
- subida brusca de humedad
- caída brusca de humedad
- temperatura alta
- temperatura incoherente
- batería baja
- panel solar bajo en horario diurno
- sensor posiblemente bloqueado
- hueco temporal

Las recomendaciones deben escribirse con prudencia. No deben ser órdenes agronómicas definitivas.

## 9. Modelo predictivo

Usar clasificación.

Objetivo recomendado:

> Predecir si en las próximas 24 horas aparecerá una alerta de sequedad relativa.

Variables posibles:

- humedad media actual
- humedad mínima
- humedad máxima
- variación de humedad
- temperatura media
- temperatura máxima
- temperatura mínima
- batería
- panel solar
- hora
- día de la semana
- medias móviles

Evaluar con separación cronológica, no mezclar pasado y futuro aleatoriamente sin justificar.

Métricas:

- accuracy
- precision
- recall
- F1-score
- matriz de confusión

## 10. IFAPA-RIA opcional

Solo como extra en notebook o informe.
No crear páginas Django para IFAPA-RIA.
No hacer que la web dependa de IFAPA-RIA.

## 11. Despliegue recomendado

Usar PythonAnywhere por ser más sencillo para empezar con Django.
Preparar:

- requirements.txt
- .env.example
- ALLOWED_HOSTS configurable
- STATIC_ROOT
- collectstatic
- README con pasos de despliegue

## 12. Entregables

- Código Django.
- Notebook de análisis.
- Modelo predictivo entrenado o script reproducible.
- README completo.
- URL pública de despliegue.
- Vídeo explicativo.
