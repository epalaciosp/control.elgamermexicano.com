/**
 * El Gamer MX — Guía Emby
 * Code Snippets: PHP / Run everywhere / Priority 10.
 * La página /emby/ debe contener únicamente: [egm_emby]
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_shortcode( 'egm_emby', function () {
    $icon_url    = 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/Captura-de-pantalla-2026-08-20-a-las-12.03.16-a.m.png';
    $android_url = 'https://play.google.com/store/apps/details?id=com.mb.android';
    $ios_url     = 'https://apps.apple.com/app/emby/id992180193';
    $desktop_url = 'https://emby.media/emby-theater.html';
    $channel_url = 'https://whatsapp.com/channel/0029VaszHAC1nozBMySSkz3X';

    ob_start();
    ?>
    <style>
        html, body { margin:0!important; background:#06090d!important; }
        body:has(.egme-page) header.wp-block-template-part,
        body:has(.egme-page) footer.wp-block-template-part,
        body:has(.egme-page) .entry-title,
        body:has(.egme-page) .wp-block-post-title { display:none!important; }
        body:has(.egme-page) .wp-site-blocks,
        body:has(.egme-page) main,
        body:has(.egme-page) .entry-content,
        body:has(.egme-page) .wp-block-post-content { width:100%!important; max-width:none!important; margin:0!important; padding:0!important; background:transparent!important; }

        .egme-page, .egme-page * { box-sizing:border-box; }
        .egme-page {
            --green:#28d26f; --green2:#51e58d; --whatsapp:#25d366;
            --panel:#0d151b; --line:#27384a; --text:#f6f9fc; --muted:#9eacbe;
            min-height:100vh; padding:30px 0 78px; color:var(--text);
            font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
            background:radial-gradient(circle at 50% -120px,rgba(40,210,111,.14),transparent 34rem),linear-gradient(180deg,#080d12,#05080c);
        }
        .egme-shell { width:min(1040px,calc(100% - 40px)); margin:0 auto; }
        .egme-back { display:inline-flex; align-items:center; gap:8px; margin-bottom:22px; color:#9eacbf!important; font-size:14px; font-weight:800; text-decoration:none!important; transition:.2s ease; }
        .egme-back:hover { color:#fff!important; transform:translateX(-3px); }

        .egme-hero { display:grid; grid-template-columns:150px 1fr; overflow:hidden; border:1px solid var(--line); border-radius:22px; background:linear-gradient(135deg,rgba(17,27,34,.98),rgba(9,15,20,.98)); box-shadow:0 24px 65px rgba(0,0,0,.28); }
        .egme-logo { position:relative; min-height:235px; display:grid; place-items:center; background:linear-gradient(145deg,#2bd878,#079648); }
        .egme-logo:after { content:""; position:absolute; inset:0; opacity:.25; background:repeating-linear-gradient(135deg,transparent 0 15px,rgba(255,255,255,.15) 16px,transparent 17px 31px); }
        .egme-logo-box { position:relative; z-index:1; width:100px; height:100px; padding:8px; display:grid; place-items:center; overflow:hidden; border-radius:21px; background:#fff; box-shadow:0 17px 38px rgba(0,64,28,.34); }
        .egme-logo-box img { width:100%!important; height:100%!important; object-fit:contain!important; display:block!important; }
        .egme-hero-body { padding:27px 30px 25px; }
        .egme-label { color:#9aa8ba; font-size:11px; font-weight:900; letter-spacing:.15em; text-transform:uppercase; }
        .egme-hero h1 { margin:7px 0 8px!important; color:#fff!important; font-size:clamp(27px,4vw,36px)!important; line-height:1.15!important; letter-spacing:-.025em; }
        .egme-hero p { margin:0!important; color:#9eacbe!important; font-size:16px!important; line-height:1.55!important; }
        .egme-channel { display:flex; align-items:center; justify-content:center; gap:9px; width:100%; margin-top:18px; padding:13px 18px; border-radius:12px; color:#06150c!important; font-size:14px; font-weight:900; text-decoration:none!important; background:var(--whatsapp); transition:.2s ease; }
        .egme-channel:hover { transform:translateY(-2px); box-shadow:0 12px 27px rgba(37,211,102,.18); }
        .egme-tags { display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
        .egme-tag { display:inline-flex; align-items:center; gap:7px; padding:8px 11px; border:1px solid #2b394b; border-radius:999px; color:#a2afbf; font-size:12px; }
        .egme-check { width:15px; height:15px; display:grid; place-items:center; border-radius:50%; color:#06140b; font-size:9px; font-weight:950; background:var(--green); }

        .egme-notice { margin:15px 0 18px; padding:16px 19px; border-left:4px solid var(--green); border-radius:12px; color:#a9bdaf; font-size:14px; line-height:1.55; background:linear-gradient(90deg,rgba(20,76,47,.60),rgba(17,45,32,.78)); }
        .egme-notice strong { color:#fff; }
        .egme-choices { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin-bottom:19px; }
        .egme-choice { display:flex; align-items:center; gap:17px; padding:21px; border:1px solid #28384a; border-radius:16px; color:inherit!important; text-decoration:none!important; background:#0d151b; transition:.23s ease; }
        .egme-choice:hover { transform:translateY(-3px); border-color:var(--green); box-shadow:0 15px 32px rgba(0,0,0,.2); }
        .egme-choice-icon { width:48px; height:48px; flex:0 0 auto; display:grid; place-items:center; border-radius:14px; color:#06130b; font-size:23px; font-weight:900; background:linear-gradient(145deg,#56ec93,#1ebd62); }
        .egme-choice h2 { margin:0 0 4px!important; color:#fff!important; font-size:18px!important; }
        .egme-choice p { margin:0!important; color:#96a4b6!important; font-size:13px!important; line-height:1.5!important; }

        .egme-heading { margin:34px 2px 16px; }
        .egme-heading small { color:var(--green2); font-size:10px; font-weight:900; letter-spacing:.15em; text-transform:uppercase; }
        .egme-heading h2 { margin:6px 0 0!important; color:#fff!important; font-size:27px!important; }
        .egme-section { margin-top:11px; overflow:hidden; border:1px solid #253547; border-radius:14px; background:rgba(13,21,27,.96); transition:.2s ease; }
        .egme-section[open] { border-color:rgba(40,210,111,.58); box-shadow:0 15px 34px rgba(0,0,0,.18); }
        .egme-section summary { position:relative; display:flex; align-items:center; gap:13px; padding:18px 52px 18px 20px; color:#fff; font-size:16px; font-weight:850; cursor:pointer; list-style:none; }
        .egme-section summary::-webkit-details-marker { display:none; }
        .egme-section summary:after { content:"+"; position:absolute; right:20px; top:50%; transform:translateY(-50%); color:#718096; font-size:23px; }
        .egme-section[open] summary:after { content:"−"; color:var(--green2); }
        .egme-device { width:31px; color:var(--green2); font-size:20px; text-align:center; }
        .egme-content { padding:5px 24px 25px; border-top:1px solid #202e3c; }
        .egme-content p { color:#a7b3c2!important; font-size:15px!important; line-height:1.65!important; }
        .egme-content h3 { margin:22px 0 8px!important; color:#fff!important; font-size:18px!important; }
        .egme-content ol { margin:18px 0 4px; padding-left:23px; }
        .egme-content li { margin:10px 0; padding-left:4px; color:#b5bfcc; font-size:15px; line-height:1.55; }
        .egme-content li::marker { color:var(--green2); font-weight:900; }
        .egme-button { display:inline-flex; align-items:center; gap:8px; margin:11px 0 5px; padding:12px 17px; border-radius:10px; color:#06140b!important; font-size:14px; font-weight:900; text-decoration:none!important; background:linear-gradient(135deg,#56e990,#25c768); transition:.2s ease; }
        .egme-button:hover { transform:translateY(-2px); box-shadow:0 12px 26px rgba(40,210,111,.2); }
        .egme-help { margin:15px 0 4px; padding:14px 16px; border:1px solid #31513f; border-radius:11px; color:#a9c2b2; font-size:14px; line-height:1.6; background:#10271b; }
        .egme-help strong { color:#79efa7; }

        @media(max-width:760px){
            .egme-page{padding-top:18px}.egme-shell{width:min(100% - 26px,540px)}.egme-hero{grid-template-columns:1fr}.egme-logo{min-height:132px}.egme-logo-box{width:84px;height:84px}.egme-hero-body{padding:22px 19px}.egme-hero h1{font-size:27px!important}.egme-choices{grid-template-columns:1fr}
        }
        @media(max-width:460px){.egme-section summary{padding:17px 46px 17px 16px;font-size:15px}.egme-content{padding:4px 18px 21px}.egme-choice{padding:17px}}
        @media(prefers-reduced-motion:reduce){.egme-back,.egme-channel,.egme-choice,.egme-button,.egme-section{transition:none}}
    </style>

    <main class="egme-page" aria-labelledby="egme-title">
        <div class="egme-shell">
            <a class="egme-back" href="<?php echo esc_url( home_url( '/' ) ); ?>">← Centro de Apps</a>

            <section class="egme-hero">
                <div class="egme-logo"><div class="egme-logo-box"><img src="<?php echo esc_url( $icon_url ); ?>" alt="Logo de Emby" loading="eager" decoding="async"></div></div>
                <div class="egme-hero-body">
                    <span class="egme-label">Guía oficial</span>
                    <h1 id="egme-title">Guía Completa de Activación Emby</h1>
                    <p>Configura tu cuenta fácilmente en todos tus dispositivos y disfruta de tu contenido al instante.</p>
                    <a class="egme-channel" href="<?php echo esc_url( $channel_url ); ?>" target="_blank" rel="noopener noreferrer">◉ Canal de El Gamer Mexicano</a>
                    <div class="egme-tags" aria-label="Información del canal"><span class="egme-tag"><span class="egme-check">✓</span> Contenido nuevo</span><span class="egme-tag"><span class="egme-check">✓</span> Noticias</span><span class="egme-tag"><span class="egme-check">✓</span> Estado del servicio</span></div>
                </div>
            </section>

            <div class="egme-notice"><strong>Recomendación:</strong> sigue los pasos indicados para evitar errores durante la activación de tu cuenta.</div>

            <nav class="egme-choices" aria-label="Contenido de la guía">
                <a class="egme-choice" href="#instrucciones"><span class="egme-choice-icon" aria-hidden="true">▣</span><div><h2>Instrucciones</h2><p>Configuración paso a paso en todos tus dispositivos.</p></div></a>
                <a class="egme-choice" href="<?php echo esc_url( home_url( '/channels/' ) ); ?>"><span class="egme-choice-icon" aria-hidden="true">▭</span><div><h2>Canales</h2><p>Abre el catálogo completo con búsqueda y filtros.</p></div></a>
            </nav>

            <section id="instrucciones" aria-labelledby="egme-instructions-title">
                <div class="egme-heading"><small>Configuración</small><h2 id="egme-instructions-title">Instrucciones por dispositivo</h2></div>

                <details class="egme-section"><summary><span class="egme-device" aria-hidden="true">●</span>Android</summary><div class="egme-content"><a class="egme-button" href="<?php echo esc_url( $android_url ); ?>" target="_blank" rel="noopener noreferrer">↓ Descargar APP</a><ol><li>Abre Emby y selecciona <strong>Next o Siguiente</strong>.</li><li>En <strong>Sign in with Emby Connect</strong>, selecciona <strong>Skip u Omitir</strong>.</li><li>Introduce la URL proporcionada por tu proveedor.</li><li>Selecciona <strong>Connect o Conectar</strong>.</li><li>Ingresa tu usuario y contraseña.</li><li>¡Todo listo para disfrutar!</li></ol></div></details>

                <details class="egme-section"><summary><span class="egme-device" aria-hidden="true">◆</span>iOS — iPhone y iPad</summary><div class="egme-content"><a class="egme-button" href="<?php echo esc_url( $ios_url ); ?>" target="_blank" rel="noopener noreferrer">↓ Descargar APP</a><ol><li>Abre Emby y selecciona <strong>Next o Siguiente</strong>.</li><li>En <strong>Sign in with Emby Connect</strong>, selecciona <strong>Skip u Omitir</strong>.</li><li>Introduce la URL proporcionada por tu proveedor.</li><li>Selecciona <strong>Connect o Conectar</strong>.</li><li>Ingresa tu usuario y contraseña.</li><li>¡Todo listo para disfrutar!</li></ol></div></details>

                <details class="egme-section"><summary><span class="egme-device" aria-hidden="true">▭</span>Smart TV</summary><div class="egme-content"><ol><li>Descarga Emby desde la tienda de aplicaciones de tu televisión.</li><li>Abre la app y selecciona <strong>Conectar a un servidor</strong>.</li><li>Introduce la URL proporcionada por tu proveedor.</li><li>Ingresa tu usuario y contraseña.</li><li>Ya puedes acceder a todo el contenido.</li></ol></div></details>

                <details class="egme-section"><summary><span class="egme-device" aria-hidden="true">▣</span>PC o Mac</summary><div class="egme-content"><a class="egme-button" href="<?php echo esc_url( $desktop_url ); ?>" target="_blank" rel="noopener noreferrer">↓ Descargar Emby Theater</a><ol><li>Abre la aplicación y selecciona <strong>Next o Siguiente</strong>.</li><li>En <strong>Sign in with Emby Connect</strong>, selecciona <strong>Skip u Omitir</strong>.</li><li>Introduce la URL proporcionada por tu proveedor.</li><li>Selecciona <strong>Connect o Conectar</strong>.</li><li>Ingresa tu usuario y contraseña.</li><li>¡Todo listo para disfrutar!</li></ol></div></details>

                <details class="egme-section"><summary><span class="egme-device" aria-hidden="true">◎</span>Navegador web</summary><div class="egme-content"><ol><li>Abre Chrome, Edge, Safari o tu navegador preferido.</li><li>Ingresa la URL del servidor proporcionada por tu proveedor.</li><li>Escribe tu usuario y contraseña.</li><li>Disfruta de tu contenido sin instalar otra aplicación.</li></ol></div></details>

                <details class="egme-section"><summary><span class="egme-device" aria-hidden="true">▭</span>Roku</summary><div class="egme-content"><ol><li>Desde la pantalla de inicio de Roku, selecciona <strong>Canales de transmisión</strong>.</li><li>Busca <strong>Emby</strong> en la tienda de canales.</li><li>Añade el canal Emby y ábrelo.</li><li>Selecciona <strong>Next o Siguiente</strong>.</li><li>En <strong>Sign in with Emby Connect</strong>, selecciona <strong>Skip u Omitir</strong>.</li><li>Introduce la URL proporcionada por tu proveedor.</li><li>Selecciona <strong>Connect o Conectar</strong>.</li><li>Ingresa tu usuario y contraseña.</li><li>¡Todo listo para disfrutar!</li></ol></div></details>

                <details class="egme-section"><summary><span class="egme-device" aria-hidden="true">a</span>Amazon Fire TV</summary><div class="egme-content"><ol><li>En la pantalla de inicio de Fire TV, selecciona <strong>Buscar</strong>.</li><li>Escribe <strong>Emby</strong> y descarga la aplicación.</li><li>Abre la app y selecciona <strong>Next o Siguiente</strong>.</li><li>En <strong>Sign in with Emby Connect</strong>, selecciona <strong>Skip u Omitir</strong>.</li><li>Introduce la URL proporcionada por tu proveedor.</li><li>Selecciona <strong>Connect o Conectar</strong>.</li><li>Ingresa tu usuario y contraseña.</li><li>¡Todo listo para disfrutar!</li></ol></div></details>

                <details class="egme-section"><summary><span class="egme-device" aria-hidden="true">!</span>Soluciones a errores comunes Emby</summary><div class="egme-content"><h3>“No se puede conectar al servidor”</h3><ol><li>Verifica que la URL del servidor sea correcta.</li><li>Comprueba tu conexión a internet.</li><li>Cierra y vuelve a abrir la aplicación.</li><li>Contacta a tu proveedor si el problema persiste.</li></ol><h3>“Credenciales incorrectas”</h3><ol><li>Verifica que el usuario y la contraseña sean correctos.</li><li>Comprueba que no existan espacios adicionales.</li><li>Escribe las credenciales manualmente.</li><li>Contacta a tu proveedor si el problema persiste.</li></ol><div class="egme-help"><strong>Consejo:</strong> copia la URL exactamente como fue enviada, incluyendo <strong>http://</strong> o <strong>https://</strong> y el puerto cuando corresponda.</div></div></details>
            </section>
        </div>
    </main>
    <?php
    return ob_get_clean();
} );
