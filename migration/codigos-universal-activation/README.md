# Universal+ — alias de activación

El portal PHP consulta el API TMail en correos.elgamermexicano.com. Tanto
inbox.php como message.php usan una whitelist idéntica de 13 asuntos; ninguno
era Universal+. No existía extracción Universal+ en este portal. No confundir
esta aplicación con el parser Partner de MyPlataforma.

Este paquete añade exclusivamente el alias «Universal+ Código de activación»
con remitente exacto no-reply@universalplus.com. Normaliza UTF-8/NFC, mayúsculas
y espacios Unicode. Mantiene intactos los 13 asuntos anteriores y sus filtros.

La extracción nueva conserva el formato certificado [A-Z0-9]{6}; busca texto
visible, omite scripts/styles/atributos y rechaza ambigüedad. El código se muestra
directamente en la bandeja y en el detalle, escapado, sin logging ni persistencia.
La bandeja prioriza el primer mensaje válido según orden API descendente. No hay
redirección automática ni consultas adicionales para extraer el código.

Política temporal observada: no hay filtro por minutos; API obtiene los últimos
15 mensajes y el listado conserva cinco asuntos permitidos. No se amplía ni se
introduce una ventana nueva. La disponibilidad de uni5 se acredita por dominio
vepquim.com permitido y local part válido, no por un alta o cambio de cuenta.

Fixture sintética: 41 checks de normalización/remitente/parser/render y 35 casos
de integración en las plantillas PHP originales, incluyendo los 13 asuntos
anteriores en ambos entrypoints y selección del código más reciente. El harness
ejecuta después del fetch, con cURL/IMAP deshabilitados. Las credenciales inline
de los originales nunca se exportan al repositorio o al reporte.

portal_patch.py exige hashes de los dos archivos productivos revisados y preserva
sus bytes de configuración. deploy_portal.py exige el resultado hash del ensayo,
respalda originales root-only fuera del document root y aplica tres archivos
atómicamente por archivo, helper primero. Si falla un check restaura originales.
No modifica el backend de correo, .env, credenciales, cuentas, ventas ni servicios.
No requiere migración, composer, dependencias ni reinicio de PHP-FPM.

Reversión manual si fuera necesaria: verificar el manifest root-only, restaurar
inbox.php y message.php respaldados conservando uid/gid/modo, retirar solamente
el helper nuevo y repetir lint y HTTP. Nunca restaurar correos o bases de negocio
para revertir este cambio de presentación/filtro.

No almacenar correos/OTP reales en fixtures, screenshots, logs ni artefactos.
