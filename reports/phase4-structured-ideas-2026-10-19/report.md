# Propuesta estructurada — pendiente

Entrada por cruce EMA/SMA con ventana fija y salida por crce

Hipótesis del modelo sin verificar: Se entra largo cuando una EMA de ventana 20 cruza por encima de una SMA de ventana 60 en la observación actual, y se sale al siguiente cruce inverso detectado.

Entrada: `ema(window=20, lag=0) crosses_above sma(window=60, lag=0)`.
Salida: `ema(window=20, lag=1) crosses_below sma(window=60, lag=1)`.

Estado: pending_semantic_review. Sin señales, simulaciones o resultados.
