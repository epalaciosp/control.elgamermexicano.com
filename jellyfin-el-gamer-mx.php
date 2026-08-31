/**
 * El Gamer MX — Guía Jellyfin
 * Code Snippets: PHP / Run everywhere / Priority 10.
 * La página /jellyfin/ debe contener únicamente: [egm_jellyfin]
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_shortcode( 'egm_jellyfin', function () {
    $icon_url    = 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/Captura-de-pantalla-2026-08-20-a-las-12.03.03-a.m.png';
    $android_url = 'https://play.google.com/store/apps/details?id=org.jellyfin.mobile';
    $ios_url     = 'https://apps.apple.com/app/jellyfin/id1480192618';
    $channel_url = 'https://whatsapp.com/channel/0029VaszHAC1nozBMySSkz3X';

    ob_start();
    ?>
    <style>
        html, body { margin: 0 !important; background: #06080d !important; }
        body:has(.egmj-page) header.wp-block-template-part,
        body:has(.egmj-page) footer.wp-block-template-part,
        body:has(.egmj-page) .entry-title,
        body:has(.egmj-page) .wp-block-post-title { display: none !important; }
        body:has(.egmj-page) .wp-site-blocks,
        body:has(.egmj-page) main,
        body:has(.egmj-page) .entry-content,
        body:has(.egmj-page) .wp-block-post-content { width: 100% !important; max-width: none !important; margin: 0 !important; padding: 0 !important; background: transparent !important; }

        .egmj-page, .egmj-page * { box-sizing: border-box; }
        .egmj-page {
            --purple:#a14dff; --purple2:#c177ff; --blue:#00a4dc; --green:#25d366;
            --panel:#0d141d; --line:#283549; --text:#f6f8fc; --muted:#9ba9bc;
            min-height:100vh; padding:30px 0 78px; color:var(--text);
            font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
            background:radial-gradient(circle at 50% -120px,rgba(161,77,255,.16),transparent 34rem),linear-gradient(180deg,#080c13,#05070b);
        }
        .egmj-shell { width:min(1040px,calc(100% - 40px)); margin:0 auto; }
        .egmj-back { display:inline-flex; align-items:center; gap:8px; margin-bottom:22px; color:#9eacbf!important; font-size:14px; font-weight:800; text-decoration:none!important; transition:.2s ease; }
        .egmj-back:hover { color:#fff!important; transform:translateX(-3px); }

        .egmj-hero { display:grid; grid-template-columns:150px 1fr; overflow:hidden; border:1px solid var(--line); border-radius:22px; background:linear-gradient(135deg,rgba(18,25,35,.98),rgba(10,15,22,.98)); box-shadow:0 24px 65px rgba(0,0,0,.28); }
        .egmj-logo { min-height:235px; display:grid; place-items:center; background:linear-gradient(145deg,#ba5bff,#6d20d6); }
        .egmj-logo-box { width:100px; height:100px; padding:8px; display:grid; place-items:center; overflow:hidden; border-radius:21px; background:#fff; box-shadow:0 17px 38px rgba(40,5,72,.35); }
        .egmj-logo-box img { width:100%!important; height:100%!important; object-fit:contain!important; display:block!important; }
        .egmj-hero-body { padding:27px 30px 25px; }
        .egmj-label { color:#9aa8ba; font-size:11px; font-weight:900; letter-spacing:.15em; text-transform:uppercase; }
        .egmj-hero h1 { margin:7px 0 8px!important; color:#fff!important; font-size:clamp(27px,4vw,36px)!important; line-height:1.15!important; letter-spacing:-.025em; }
        .egmj-hero p { margin:0!important; color:#9eacbe!important; font-size:16px!important; line-height:1.55!important; }
        .egmj-channel { display:flex; align-items:center; justify-content:center; gap:9px; width:100%; margin-top:18px; padding:13px 18px; border-radius:12px; color:#06150c!important; font-size:14px; font-weight:900; text-decoration:none!important; background:var(--green); transition:.2s ease; }
        .egmj-channel:hover { transform:translateY(-2px); box-shadow:0 12px 27px rgba(37,211,102,.18); }
        .egmj-tags { display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
        .egmj-tag { display:inline-flex; align-items:center; gap:7px; padding:8px 11px; border:1px solid #2b394b; border-radius:999px; color:#a2afbf; font-size:12px; }
        .egmj-check { width:15px; height:15px; display:grid; place-items:center; border-radius:50%; color:#06140b; font-size:9px; font-weight:950; background:#26d574; }

        .egmj-notice { margin:15px 0 18px; padding:16px 19px; border-left:4px solid var(--purple); border-radius:12px; color:#aea9c2; font-size:14px; line-height:1.55; background:linear-gradient(90deg,rgba(72,39,105,.62),rgba(32,24,44,.82)); }
        .egmj-notice strong { color:#fff; }
        .egmj-choices { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin-bottom:19px; }
        .egmj-choice { display:flex; align-items:center; gap:17px; padding:21px; border:1px solid #28364a; border-radius:16px; color:inherit!important; text-decoration:none!important; background:#0d141c; transition:.23s ease; }
        .egmj-choice:hover { transform:translateY(-3px); border-color:var(--purple); box-shadow:0 15px 32px rgba(0,0,0,.2); }
        .egmj-choice-icon { width:48px; height:48px; flex:0 0 auto; display:grid; place-items:center; border-radius:14px; color:#fff; font-size:23px; font-weight:900; background:linear-gradient(145deg,#b45cff,#6d27cc); }
        .egmj-choice h2 { margin:0 0 4px!important; color:#fff!important; font-size:18px!important; }
        .egmj-choice p { margin:0!important; color:#96a4b6!important; font-size:13px!important; line-height:1.5!important; }

        .egmj-heading { margin:34px 2px 16px; }
        .egmj-heading small { color:var(--purple2); font-size:10px; font-weight:900; letter-spacing:.15em; text-transform:uppercase; }
        .egmj-heading h2 { margin:6px 0 0!important; color:#fff!important; font-size:27px!important; }
        .egmj-heading p { margin:7px 0 0!important; color:#96a4b6!important; font-size:14px!important; }

        .egmj-section { margin-top:11px; overflow:hidden; border:1px solid #253346; border-radius:14px; background:rgba(13,20,29,.96); }
        .egmj-section[open] { border-color:rgba(161,77,255,.58); box-shadow:0 15px 34px rgba(0,0,0,.18); }
        .egmj-section summary { position:relative; display:flex; align-items:center; gap:13px; padding:18px 52px 18px 20px; color:#fff; font-size:16px; font-weight:850; cursor:pointer; list-style:none; }
        .egmj-section summary::-webkit-details-marker { display:none; }
        .egmj-section summary:after { content:"+"; position:absolute; right:20px; top:50%; transform:translateY(-50%); color:#718096; font-size:23px; }
        .egmj-section[open] summary:after { content:"−"; color:var(--purple2); }
        .egmj-device { width:31px; color:var(--purple2); font-size:20px; text-align:center; }
        .egmj-content { padding:5px 24px 25px; border-top:1px solid #202c3b; }
        .egmj-content p { color:#a7b3c2!important; font-size:15px!important; line-height:1.65!important; }
        .egmj-content ol { margin:18px 0 4px; padding-left:23px; }
        .egmj-content li { margin:10px 0; padding-left:4px; color:#b5bfcc; font-size:15px; line-height:1.55; }
        .egmj-content li::marker { color:var(--purple2); font-weight:900; }
        .egmj-button { display:inline-flex; align-items:center; gap:8px; margin:11px 0 5px; padding:12px 17px; border-radius:10px; color:#fff!important; font-size:14px; font-weight:900; text-decoration:none!important; background:linear-gradient(135deg,#b75fff,#7629da); transition:.2s ease; }
        .egmj-button:hover { transform:translateY(-2px); box-shadow:0 12px 26px rgba(161,77,255,.22); }
        .egmj-code { display:inline-block; padding:5px 9px; border:1px solid #3a4960; border-radius:7px; color:#fff; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; background:#101a27; }

        @media(max-width:760px){
            .egmj-shell{width:min(100% - 26px,540px)} .egmj-hero{grid-template-columns:1fr}.egmj-logo{min-height:132px}.egmj-logo-box{width:84px;height:84px}.egmj-hero-body{padding:22px 19px}.egmj-hero h1{font-size:27px!important}.egmj-choices{grid-template-columns:1fr}
        }
        @media(max-width:460px){.egmj-section summary{padding:17px 46px 17px 16px;font-size:15px}.egmj-content{padding:4px 18px 21px}}
        @media(prefers-reduced-motion:reduce){.egmj-back,.egmj-channel,.egmj-choice,.egmj-button{transition:none}}
    </style>

    <main class="egmj-page" aria-labelledby="egmj-title">
        <div class="egmj-shell">
            <a class="egmj-back" href="<?php echo esc_url( home_url( '/' ) ); ?>">← Centro de Apps</a>

            <section class="egmj-hero">
                <div class="egmj-logo"><div class="egmj-logo-box"><img src="<?php echo esc_url( $icon_url ); ?>" alt="" loading="eager" decoding="async"></div></div>
                <div class="egmj-hero-body">
                    <span class="egmj-label">Guía oficial</span>
                    <h1 id="egmj-title">Guía Completa de Activación Jellyfin</h1>
                    <p>Configura tu cuenta fácilmente en todos tus dispositivos y disfruta de tu contenido al instante.</p>
                    <a class="egmj-channel" href="<?php echo esc_url( $channel_url ); ?>" target="_blank" rel="noopener noreferrer">◉ Canal de El Gamer Mexicano</a>
                    <div class="egmj-tags"><span class="egmj-tag"><span class="egmj-check">✓</span> Contenido nuevo</span><span class="egmj-tag"><span class="egmj-check">✓</span> Noticias</span><span class="egmj-tag"><span class="egmj-check">✓</span> Estado del servicio</span></div>
                </div>
            </section>

            <div class="egmj-notice"><strong>Recomendación:</strong> sigue los pasos indicados para evitar errores durante la configuración de tu cuenta.</div>

            <nav class="egmj-choices" aria-label="Contenido de la guía">
                <a class="egmj-choice" href="#instrucciones"><span class="egmj-choice-icon" aria-hidden="true">▣</span><div><h2>Instrucciones</h2><p>Configuración paso a paso en celulares, televisores y computadora.</p></div></a>
                <a class="egmj-choice" href="<?php echo esc_url( home_url( '/channels/' ) ); ?>"><span class="egmj-choice-icon" aria-hidden="true">▭</span><div><h2>Canales</h2><p>Abre el catálogo completo con búsqueda y filtros.</p></div></a>
            </nav>

            <section id="instrucciones" aria-labelledby="egmj-instructions-title">
                <div class="egmj-heading"><small>Configuración</small><h2 id="egmj-instructions-title">Instrucciones por dispositivo</h2></div>

                <details class="egmj-section"><summary><span class="egmj-device">●</span>Android</summary><div class="egmj-content"><a class="egmj-button" href="<?php echo esc_url( $android_url ); ?>" target="_blank" rel="noopener noreferrer">↓ Descargar APP</a><ol><li>Descarga Jellyfin desde Google Play.</li><li>Abre la aplicación y, en <strong>Servidor o Host</strong>, introduce la URL proporcionada.</li><li>Pulsa <strong>Conectar</strong>.</li><li>Ingresa tu usuario y contraseña.</li><li>¡Todo listo para disfrutar!</li></ol></div></details>

                <details class="egmj-section"><summary><span class="egmj-device">◆</span>iOS — iPhone y iPad</summary><div class="egmj-content"><a class="egmj-button" href="<?php echo esc_url( $ios_url ); ?>" target="_blank" rel="noopener noreferrer">↓ Descargar APP</a><ol><li>Descarga Jellyfin desde App Store.</li><li>Abre la aplicación e introduce la URL proporcionada en <strong>Servidor o Host</strong>.</li><li>Pulsa <strong>Conectar</strong>.</li><li>Ingresa tu usuario y contraseña.</li><li>¡Todo listo para disfrutar!</li></ol></div></details>

                <details class="egmj-section"><summary><span class="egmj-device">▭</span>Smart TV</summary><div class="egmj-content"><ol><li>Descarga Jellyfin desde la tienda de aplicaciones de tu TV.</li><li>Abre la app y selecciona <strong>Ingresar la dirección del servidor/Host</strong>.</li><li>Introduce la URL proporcionada y pulsa <strong>Conectar</strong>.</li><li>Selecciona <strong>Agregar cuenta/Add account</strong>.</li><li>Ingresa tu usuario y contraseña.</li><li>Ya puedes acceder al contenido.</li></ol></div></details>

                <details class="egmj-section"><summary><span class="egmj-device">◎</span>Smart TV — Opción con navegador</summary><div class="egmj-content"><ol><li>Abre el navegador de tu televisión.</li><li>Ingresa la URL proporcionada.</li><li>Escribe tus credenciales de acceso.</li><li>Disfruta de tu contenido.</li></ol></div></details>

                <details class="egmj-section"><summary><span class="egmj-device">▣</span>PC o Mac</summary><div class="egmj-content"><ol><li>Abre Chrome, Edge, Safari o tu navegador preferido.</li><li>Ingresa la URL proporcionada.</li><li>Escribe tu usuario y contraseña.</li><li>Disfruta de tu contenido sin instalar otra aplicación.</li></ol></div></details>
            </section>

        </div>
    </main>
    <?php
    return ob_get_clean();
} );
