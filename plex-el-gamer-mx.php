/**
 * El Gamer MX — Guía Plex
 * Code Snippets: PHP / Run everywhere / Priority 10.
 * La página /plex/ debe contener únicamente: [egm_plex]
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_shortcode( 'egm_plex', function () {
    $android_url = 'https://play.google.com/store/apps/details?hl=es_CO&id=com.plexapp.android';
    $desktop_url = 'https://www.plex.tv/es/media-server-downloads/?cat=plex+desktop&plat=windows';
    $web_url     = 'https://app.plex.tv/desktop/';
    $link_url    = 'https://www.plex.tv/link/';
    $channel_url = 'https://whatsapp.com/channel/0029VaszHAC1nozBMySSkz3X';

    ob_start();
    ?>
    <style>
        html, body { margin: 0 !important; background: #06090e !important; }
        body:has(.egmp-page) header.wp-block-template-part,
        body:has(.egmp-page) footer.wp-block-template-part,
        body:has(.egmp-page) .entry-title,
        body:has(.egmp-page) .wp-block-post-title { display: none !important; }
        body:has(.egmp-page) .wp-site-blocks,
        body:has(.egmp-page) main,
        body:has(.egmp-page) .entry-content,
        body:has(.egmp-page) .wp-block-post-content { width: 100% !important; max-width: none !important; margin: 0 !important; padding: 0 !important; background: transparent !important; }

        .egmp-page, .egmp-page * { box-sizing: border-box; }
        .egmp-page {
            --gold: #e5a719; --gold2: #ffbd25; --green: #25d366;
            --panel: #0d141d; --panel2: #111923; --line: #263447;
            --text: #f7f9fc; --muted: #9caabd;
            min-height: 100vh; padding: 30px 0 78px; color: var(--text);
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background:
                radial-gradient(circle at 50% -120px, rgba(229,167,25,.13), transparent 34rem),
                linear-gradient(180deg, #080d13 0%, #05080c 100%);
        }
        .egmp-shell { width: min(1000px, calc(100% - 40px)); margin: 0 auto; }
        .egmp-back { display: inline-flex; align-items: center; gap: 9px; margin: 0 0 22px; color: #9facc0 !important; font-size: 14px; font-weight: 800; text-decoration: none !important; transition: color .2s ease, transform .2s ease; }
        .egmp-back:hover { color: #fff !important; transform: translateX(-3px); }

        .egmp-hero { display: grid; grid-template-columns: 148px 1fr; overflow: hidden; border: 1px solid var(--line); border-radius: 22px; background: linear-gradient(135deg, rgba(18,25,34,.98), rgba(10,15,22,.98)); box-shadow: 0 24px 65px rgba(0,0,0,.27); }
        .egmp-logo { position: relative; min-height: 224px; display: grid; place-items: center; background: linear-gradient(145deg, #ffbb1e, #bd6e00); }
        .egmp-logo:after { content: ""; position: absolute; inset: 0; opacity: .35; background: repeating-linear-gradient(135deg, transparent 0 13px, rgba(255,255,255,.15) 14px, transparent 15px 28px); }
        .egmp-logo-box { position: relative; z-index: 1; width: 96px; height: 96px; display: grid; place-items: center; border-radius: 20px; background: #fff; box-shadow: 0 17px 36px rgba(53,30,0,.31); }
        .egmp-wordmark { color: #05070a; font-size: 30px; font-weight: 950; letter-spacing: -2.5px; }
        .egmp-wordmark i { color: var(--gold); font-style: normal; }
        .egmp-hero-body { padding: 27px 30px 25px; }
        .egmp-label { color: #9aa8ba; font-size: 11px; font-weight: 900; letter-spacing: .15em; text-transform: uppercase; }
        .egmp-hero h1 { margin: 7px 0 8px !important; color: #fff !important; font-size: clamp(27px, 4vw, 36px) !important; line-height: 1.15 !important; letter-spacing: -.025em; }
        .egmp-hero p { margin: 0 !important; color: #9eacbe !important; font-size: 16px !important; line-height: 1.55 !important; }
        .egmp-channel { display: flex; align-items: center; justify-content: center; gap: 9px; width: 100%; margin-top: 18px; padding: 13px 18px; border-radius: 12px; color: #06150c !important; font-size: 14px; font-weight: 900; text-decoration: none !important; background: var(--green); transition: transform .2s ease, box-shadow .2s ease; }
        .egmp-channel:hover { transform: translateY(-2px); box-shadow: 0 12px 27px rgba(37,211,102,.18); }
        .egmp-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
        .egmp-tag { display: inline-flex; align-items: center; gap: 7px; padding: 8px 11px; border: 1px solid #2b394b; border-radius: 999px; color: #a2afbf; font-size: 12px; }
        .egmp-check { width: 15px; height: 15px; display: grid; place-items: center; border-radius: 50%; color: #06140b; font-size: 9px; font-weight: 950; background: #26d574; }

        .egmp-notice { margin: 15px 0 18px; padding: 16px 19px; border-left: 4px solid var(--gold); border-radius: 12px; color: #a9b5c4; font-size: 14px; line-height: 1.55; background: linear-gradient(90deg, rgba(96,62,12,.55), rgba(42,32,17,.78)); }
        .egmp-notice strong { color: #fff; }

        .egmp-section { margin-top: 11px; overflow: hidden; border: 1px solid #253346; border-radius: 14px; background: rgba(13,20,29,.96); transition: border-color .2s ease, box-shadow .2s ease; }
        .egmp-section[open] { border-color: rgba(229,167,25,.55); box-shadow: 0 15px 34px rgba(0,0,0,.18); }
        .egmp-section summary { position: relative; display: flex; align-items: center; gap: 13px; padding: 18px 52px 18px 20px; color: #fff; font-size: 16px; font-weight: 850; cursor: pointer; list-style: none; }
        .egmp-section summary::-webkit-details-marker { display: none; }
        .egmp-section summary:after { content: "+"; position: absolute; right: 20px; top: 50%; transform: translateY(-50%); color: #718096; font-size: 23px; font-weight: 400; }
        .egmp-section[open] summary:after { content: "−"; color: var(--gold2); }
        .egmp-device { width: 31px; color: var(--gold2); font-size: 21px; text-align: center; }
        .egmp-content { padding: 5px 24px 25px; border-top: 1px solid #202c3b; }
        .egmp-content p { color: #a7b3c2 !important; font-size: 15px !important; line-height: 1.65 !important; }
        .egmp-content h3 { margin: 22px 0 8px !important; color: #fff !important; font-size: 18px !important; }
        .egmp-content ol { margin: 18px 0 4px; padding-left: 23px; }
        .egmp-content li { margin: 10px 0; padding-left: 4px; color: #b5bfcc; font-size: 15px; line-height: 1.55; }
        .egmp-content li::marker { color: var(--gold2); font-weight: 900; }
        .egmp-button { display: inline-flex; align-items: center; gap: 8px; margin: 11px 0 5px; padding: 12px 17px; border-radius: 10px; color: #0a0c0f !important; font-size: 14px; font-weight: 900; text-decoration: none !important; background: linear-gradient(135deg, #ffc334, #e5a719); transition: transform .2s ease, box-shadow .2s ease; }
        .egmp-button:hover { transform: translateY(-2px); box-shadow: 0 12px 26px rgba(229,167,25,.18); }
        .egmp-warning { margin: 18px 0 8px; padding: 16px 18px; border: 1px solid #554018; border-radius: 11px; color: #d9c491; font-size: 14px; line-height: 1.6; background: #29200f; }
        .egmp-warning strong { color: #ffd469; }
        .egmp-linkbox { display: inline-block; margin: 3px 0; padding: 7px 10px; border: 1px solid #39485c; border-radius: 8px; color: #fff !important; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; text-decoration: none !important; background: #101a26; }
        .egmp-video { position: relative; aspect-ratio: 16 / 9; margin-top: 17px; overflow: hidden; border: 1px solid #303c4d; border-radius: 13px; background: #05080c; }
        .egmp-video iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }

        @media (max-width: 700px) {
            .egmp-page { padding-top: 18px; }
            .egmp-shell { width: min(100% - 26px, 520px); }
            .egmp-hero { grid-template-columns: 1fr; }
            .egmp-logo { min-height: 132px; }
            .egmp-logo-box { width: 82px; height: 82px; }
            .egmp-wordmark { font-size: 26px; }
            .egmp-hero-body { padding: 22px 19px; }
            .egmp-hero h1 { font-size: 27px !important; }
            .egmp-hero p { font-size: 15px !important; }
            .egmp-tag { font-size: 11px; }
            .egmp-section summary { padding: 17px 46px 17px 16px; font-size: 15px; }
            .egmp-content { padding: 4px 18px 21px; }
        }
        @media (prefers-reduced-motion: reduce) { .egmp-back, .egmp-channel, .egmp-button, .egmp-section { transition: none; } }
    </style>

    <main class="egmp-page" aria-labelledby="egmp-title">
        <div class="egmp-shell">
            <a class="egmp-back" href="<?php echo esc_url( home_url( '/' ) ); ?>">← Centro de Apps</a>

            <section class="egmp-hero">
                <div class="egmp-logo" aria-hidden="true"><div class="egmp-logo-box"><span class="egmp-wordmark">ple<i>›</i></span></div></div>
                <div class="egmp-hero-body">
                    <span class="egmp-label">Guía oficial</span>
                    <h1 id="egmp-title">Guía Completa de Activación PLEX</h1>
                    <p>Configura tu cuenta fácilmente en todos tus dispositivos y disfruta de tu contenido al instante.</p>
                    <a class="egmp-channel" href="<?php echo esc_url( $channel_url ); ?>" target="_blank" rel="noopener noreferrer">◉ Canal de El Gamer Mexicano</a>
                    <div class="egmp-tags" aria-label="Información del canal">
                        <span class="egmp-tag"><span class="egmp-check">✓</span> Contenido nuevo</span>
                        <span class="egmp-tag"><span class="egmp-check">✓</span> Noticias</span>
                        <span class="egmp-tag"><span class="egmp-check">✓</span> Estado del servicio</span>
                    </div>
                </div>
            </section>

            <div class="egmp-notice"><strong>Recomendación:</strong> sigue atentamente estos pasos para una activación exitosa de tu cuenta.</div>

            <details class="egmp-section">
                <summary><span class="egmp-device" aria-hidden="true">●</span>Android</summary>
                <div class="egmp-content">
                    <p>Instala la aplicación oficial de Plex desde Google Play e inicia sesión con la cuenta que te fue proporcionada.</p>
                    <a class="egmp-button" href="<?php echo esc_url( $android_url ); ?>" target="_blank" rel="noopener noreferrer">↓ Descargar APP</a>
                    <ol><li>Selecciona <strong>Descargar APP</strong>.</li><li>Instala la aplicación.</li><li>Ábrela e inicia sesión con tu cuenta PLEX.</li></ol>
                </div>
            </details>

            <details class="egmp-section">
                <summary><span class="egmp-device" aria-hidden="true">▣</span>Computador — Descargar APP</summary>
                <div class="egmp-content">
                    <p>Descarga la aplicación oficial para usar Plex directamente desde tu computadora.</p>
                    <a class="egmp-button" href="<?php echo esc_url( $desktop_url ); ?>" target="_blank" rel="noopener noreferrer">↓ Descargar APP</a>
                    <div class="egmp-warning"><strong>Advertencia importante:</strong> si la aplicación solicita descargar una versión más reciente, selecciona <strong>“No”</strong>, cierra la aplicación y vuelve a abrirla para continuar.</div>
                    <ol><li>Selecciona <strong>Descargar APP</strong>.</li><li>Instala la aplicación.</li><li>Ábrela e inicia sesión con tu cuenta PLEX.</li></ol>
                </div>
            </details>

            <details class="egmp-section">
                <summary><span class="egmp-device" aria-hidden="true">◎</span>Computador — App Web</summary>
                <div class="egmp-content">
                    <p>También puedes utilizar Plex desde el navegador sin instalar ningún programa.</p>
                    <a class="egmp-button" href="<?php echo esc_url( $web_url ); ?>" target="_blank" rel="noopener noreferrer">↗ Usar App Web</a>
                    <ol><li>Abre el enlace en tu navegador.</li><li>Selecciona <strong>Sign In</strong> o <strong>Iniciar sesión</strong>.</li><li>Abre <a class="egmp-linkbox" href="<?php echo esc_url( $link_url ); ?>" target="_blank" rel="noopener noreferrer">plex.tv/link</a>.</li><li>Inicia sesión con tu cuenta PLEX.</li><li>Ingresa el código proporcionado por la App Web y confirma.</li></ol>
                </div>
            </details>

            <details class="egmp-section">
                <summary><span class="egmp-device" aria-hidden="true">▭</span>Smart TV y consolas</summary>
                <div class="egmp-content">
                    <ol><li>Abre la tienda de aplicaciones de tu Smart TV o consola.</li><li>Busca e instala la aplicación PLEX.</li><li>Abre Plex y selecciona <strong>Iniciar sesión</strong> o <strong>Sign In</strong>.</li><li>Desde otro dispositivo, abre <a class="egmp-linkbox" href="<?php echo esc_url( $link_url ); ?>" target="_blank" rel="noopener noreferrer">plex.tv/link</a>.</li><li>Inicia sesión con tu cuenta PLEX.</li><li>Ingresa el código mostrado en la TV y confirma.</li><li>Recarga la página dos veces para actualizar el usuario.</li></ol>
                    <h3>Vincular PLEX a tu TV: instrucciones paso a paso</h3>
                    <div class="egmp-video"><iframe src="https://www.youtube-nocookie.com/embed/vgaWlwbC3sE" title="Cómo vincular Plex a una televisión" loading="lazy" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>
                </div>
            </details>

            <details class="egmp-section">
                <summary><span class="egmp-device" aria-hidden="true">!</span>Soluciones a errores comunes PLEX</summary>
                <div class="egmp-content">
                    <h3>“Ha ocurrido un error al intentar reproducir este video”</h3>
                    <p>Consulta el siguiente video para revisar la solución recomendada paso a paso.</p>
                    <div class="egmp-video"><iframe src="https://www.youtube-nocookie.com/embed/EeboPZuLGjM" title="Solución a error de reproducción de Plex" loading="lazy" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>
                </div>
            </details>
        </div>
    </main>
    <?php
    return ob_get_clean();
} );
