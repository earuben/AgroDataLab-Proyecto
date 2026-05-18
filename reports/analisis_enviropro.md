# Analisis EnviroPro
## Comprension inicial
- Archivo analizado: `data\processed\enviropro_completo_2024_2026.csv`
- Numero de registros: 20.284
- Numero de columnas originales: 36
- Primera lectura: 2024-01-01 16:00:00
- Ultima lectura: 2026-04-29 16:00:00
- La fecha/hora se interpreta con `pd.to_datetime`; el CSV ya usa punto decimal, no coma decimal.
- Humedad y temperatura se analizan por sensores S1-S8; bateria y panel solar vienen en mV y se convierten a V.

## Limpieza y calidad de datos
- Duplicados exactos: 0
- Fechas duplicadas: 0
- Frecuencia aproximada mas habitual: 0 days 01:00:00
- Huecos temporales mayores de 2 horas: 4 (maximo 1 days 00:00:00)
- Temperaturas incoherentes por rango > 18 C: 705
- Lecturas con posible fallo energetico: 10797
- humedad_menor_0: 0
- humedad_mayor_100: 63
- temperatura_menor_-20: 0
- temperatura_mayor_60: 0
- bateria_no_positiva: 0
- panel_no_positivo: 9782

## Interpretacion de visualizaciones
- `reports\figures\01_humedad_media_temporal.png`: La humedad media permite localizar periodos secos y recuperaciones tras posibles aportes de agua.
- `reports\figures\02_temperatura_media_temporal.png`: La temperatura media muestra la estacionalidad esperada y ayuda a contextualizar la sequedad.
- `reports\figures\03_bateria_temporal.png`: La bateria en V permite detectar etapas de riesgo energetico del nodo.
- `reports\figures\04_panel_solar_temporal.png`: El panel solar presenta variabilidad diaria y sirve para revisar carga o sombras.
- `reports\figures\05_humedad_por_sensor.png`: La comparacion por sensor muestra diferencias por profundidad o ubicacion y sensores que conviene revisar.
- `reports\figures\06_temperatura_por_sensor.png`: La temperatura promedio por sensor ayuda a detectar sensores con comportamiento distinto.
- `reports\figures\07_humedad_semanal.png`: La serie semanal suaviza ruido horario y deja ver tendencias de humedad defendibles.
- `reports\figures\08_temperatura_semanal.png`: La temperatura semanal resume la evolucion termica sin depender de lecturas puntuales.
- `reports\figures\09_correlacion_humedad_temperatura.png`: La matriz resume relaciones lineales entre humedad, temperatura y energia.
- `reports\figures\10_dispersion_humedad_temperatura.png`: La dispersion permite ver si temperaturas altas coinciden con humedades bajas.
- `reports\figures\11_alertas_por_dia.png`: Las alertas por dia concentran los periodos que requieren revision prioritaria.
- `reports\figures\12_nulos_por_sensor.png`: Los nulos por sensor muestran ausencias y posibles problemas de calidad de datos.
