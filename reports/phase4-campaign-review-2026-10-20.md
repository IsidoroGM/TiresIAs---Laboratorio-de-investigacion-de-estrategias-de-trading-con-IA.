# TiresIAs: revisión y plan de experimento — 20/10/2026

Se añaden `campaign_review` y `campaign_experiment` sin modificar módulos sellados
de las etapas anteriores. La revisión vincula una declaración técnica con una
captura exacta; solo una decisión aceptada admite preparar el plan de comparación.
Revisar y planificar no consultan modelos, reservan comparaciones o ejecutan cálculos.

## Pruebas verificadas

Se verificaron **48 pruebas nuevas distintas en tres pases**:

- Revisión: 30 aprobadas en 88,16 segundos.
- Planificación e integración: 17 aprobadas en 270,89 segundos.
- Compatibilidad con los ejecutores anteriores: 1 aprobada en 7,59 segundos.

No son un único pase conjunto ni una nueva suite global. Se usaron temporales
exclusivos y caché de pytest desactivada según AGENTS.md. La recolección global
identificó 1.445 pruebas en 0,72 segundos; recolectar no equivale a ejecutarlas.
La última suite global comprobada sigue siendo la de 1.253 pruebas.

Las pruebas comprobaron aceptación, rechazo y necesidad de aclaración; las seis
declaraciones booleanas; correspondencia exacta con campaña, recibo, petición,
observación y reglas; rechazo de duplicados; exclusividad entre hilos; decisiones
consumidas; fallos parciales; alteración de copias, fuentes o reservas, y prohibición
de aprobar después de reservar comparaciones. Las decisiones del revisor se
conservan como declaraciones, sin atribuirles prueba independiente de rentabilidad.

El plan preserva controles y objetivo congelados, datos de desarrollo, reglas y
presupuesto de una base y una candidata. Se comprobó el rechazo de campañas con
cero backtests, cálculos consumidos y comparaciones ya reservadas. Cambiar nombre,
criterio o carpeta conserva la identidad compartida del cálculo. Una reserva
posterior no invalida el artefacto ya registrado ni le concede permiso de ejecución.
Los ejecutores anteriores rechazan este contrato antes de calcular.

La integración usa las fuentes guiadas completas y un transporte falso, con una
regla artificial para comprobar el contrato, sin buscar o simular su rendimiento.
Bloquea red, proveedor, cálculo, nuevas reservas y evaluación exterior. Usa de forma
explícita la caché de lectura validada dentro de esa prueba; no se activa por defecto
en las API de producción. El recorrido de verificaciones sigue siendo costoso;
estos tiempos no constituyen una comparativa de rendimiento de la aplicación.

## Consulta del registro real

La auditoría `.local/campaign-review-audits/fee3b2c854f94fe0901844061da9424c` consultó
el registro de revisiones de la campaña real, que sigue inactiva y sin reservas,
capturas, revisiones o planes nuevos. No se inventó una respuesta válida para
ejercitar la aceptación en la aplicación. Esta consulta de estado no es una
comprobación completa de vigencia ni una autorización para ejecutar.

Los ocho contadores de red, proveedor, cálculo, reserva heredada, evaluación exterior,
reserva de campaña, escritura de capturas y escritura de revisión o plan quedaron
a cero. SQLite mantuvo sus bytes, los nueve archivos históricos de reservas siguen
intactos y las cinco raíces de capturas, revisiones y planes mantienen su estado.
PROJECT_STATUS.md conserva su SHA-256; la FASE 4 continúa abierta.

Se verificaron las 297 copias y referencias originales anteriores antes y después.
El [nuevo inventario](phase4-campaign-review-2026-10-20/snapshot.json) añade diez:
**307 copias y referencias entre 22 inventarios concretos**, sin presentarlas como
archivos físicos únicos. Conserva consulta, auditoría, huellas, eventos, script,
código y pruebas con nombres que pytest no recolecta.

## Consumo y continuidad

Consumo nuevo real del investigador: **0 llamadas, 0 tokens, 0 USD API y 0 backtests**.
Los 2.262 tokens de entrada y 176 de salida del intento compacto heredado, con
0 USD de API, permanecen separados; no representan el total de la aplicación.
Los proveedores, observaciones y cifras de las pruebas son artificiales.

La captura conserva un origen declarado por el llamador; aceptar su revisión no
acredita transporte o autoría. Siguen pendientes el permiso de campaña, la memoria
completa para peticiones sucesivas y el ejecutor que vincule la reserva contable
con la reserva compartida del motor. La ejecución permanece desactivada y no se
reabren intentos consumidos ni se reutiliza evaluación conocida como inédita.
No hubo instalaciones, servicios nuevos, dinero real, commits o pushes.

Uso: [revisión técnica y plan](../docs/CAMPAIGN_REVIEW.md).
