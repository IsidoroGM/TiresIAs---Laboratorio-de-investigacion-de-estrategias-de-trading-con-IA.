# FASE 6 — Preparación de JForex, 22/10/2026

Esta entrega prepara instalación y referencia de comparación; no cambia código
de la aplicación ni ejecuta estrategias. La comprobación del entorno normal de
Windows no encuentra JForex en el registro ni en los directorios habituales;
no descarta una instalación portable. Java y Maven ya están disponibles.

Se descarga desde el enlace oficial el instalador Windows 4.23 a
`.local/jforex/downloads/JForex4_windows-x64.exe` (fuera de Git), sin iniciarlo.
Authenticode confirma firma válida de SWFX SA; este informe conserva URL HTTPS,
SHA-256, tamaño y certificado público, sin incluir el ejecutable.

`bundle/` conserva el resultado Python existente, sus entradas y fills identificados
como referencia Python, la guía y una configuración de preparación. El ZIP contiene
los mismos bytes y un manifiesto con sus huellas. No incluye informes externos,
credenciales, cuenta demo, estrategia Java o resultados nuevos.

La revisión identifica una incompatibilidad de cantidad y deja un caso escalado
propuesto, sin calcular ni reemplazar la referencia anterior. Datos, sesiones,
costes y comportamiento del tester siguen pendientes de contraste. La guía enlaza
las fuentes oficiales y los pasos que debe completar el usuario para instalar y
acceder al probador.

Se verifican 14 manifiestos de 13 informes anteriores (uno corresponde al archivo
de un contraste), con todas sus evidencias, fuentes del motor,
originales de precios y huellas del resultado copiado. Se comprueban CRC y huellas
del ZIP. Cuentas, cadenas y presupuestos observados no cambian durante la preparación.
No se repite pytest: no cambia código de la aplicación. Las 630 pruebas aprobadas
corresponden al incremento anterior, cuya evidencia se conserva intacta.

Instalación, aceptación de condiciones, alta y acceso no realizados. Estrategia
Java, nuevo caso Python, informe HTML e importación nativa pendientes. Sin nuevos
backtests, llamadas al modelo, operaciones, commit o push. PROJECT_STATUS permanece
intacto y FASE 6 sigue abierta.
