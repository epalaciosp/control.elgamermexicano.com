/**
 * El Gamer MX — Guía Spotify+
 * Code Snippets: PHP / Run everywhere / Priority 10.
 * La página /spotify/ debe contener únicamente: [egm_spotify]
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_shortcode( 'egm_spotify', function () {
    // El parámetro de versión evita que el navegador o CDN reutilice la APK anterior.
    $android_url    = 'https://apps.multiplataforma.co/SpotifyPlus/SpotifyPlus.apk?v=20260826';
    $windows_url    = 'https://apps.multiplataforma.co/SpotifyPlus/SpotifyPlus-setup.exe';
    $downloader_url = 'https://aftv.news/6736378';

    ob_start();
    ?>
    <style>
        html, body { margin:0!important; background:#06090d!important; }
        body:has(.egms-page) header.wp-block-template-part,
        body:has(.egms-page) footer.wp-block-template-part,
        body:has(.egms-page) .entry-title,
        body:has(.egms-page) .wp-block-post-title { display:none!important; }
        body:has(.egms-page) .wp-site-blocks,
        body:has(.egms-page) main,
        body:has(.egms-page) .entry-content,
        body:has(.egms-page) .wp-block-post-content { width:100%!important; max-width:none!important; margin:0!important; padding:0!important; background:transparent!important; }

        .egms-page, .egms-page * { box-sizing:border-box; }
        .egms-page {
            --green:#1ed760; --green2:#54ea89; --deep:#128d3d;
            --panel:#0d151a; --line:#273747; --text:#f6f9fc; --muted:#9eacbe;
            min-height:100vh; padding:30px 0 78px; color:var(--text);
            font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
            background:radial-gradient(circle at 50% -120px,rgba(30,215,96,.14),transparent 34rem),linear-gradient(180deg,#080d12,#05080c);
        }
        .egms-shell { width:min(1040px,calc(100% - 40px)); margin:0 auto; }
        .egms-back { display:inline-flex; align-items:center; gap:8px; margin-bottom:22px; color:#9eacbf!important; font-size:14px; font-weight:800; text-decoration:none!important; transition:.2s ease; }
        .egms-back:hover { color:#fff!important; transform:translateX(-3px); }

        .egms-hero { display:grid; grid-template-columns:150px 1fr; overflow:hidden; border:1px solid var(--line); border-radius:22px; background:linear-gradient(135deg,rgba(17,27,33,.98),rgba(9,15,20,.98)); box-shadow:0 24px 65px rgba(0,0,0,.28); }
        .egms-logo { position:relative; min-height:230px; display:grid; place-items:center; background:linear-gradient(145deg,#26dd6a,#0e9d44); }
        .egms-logo:after { content:""; position:absolute; inset:0; opacity:.24; background:repeating-linear-gradient(135deg,transparent 0 15px,rgba(255,255,255,.15) 16px,transparent 17px 31px); }
        .egms-logo-box { position:relative; z-index:1; width:100px; height:100px; display:grid; place-items:center; border-radius:21px; background:#fff; box-shadow:0 17px 38px rgba(0,70,27,.35); }
        .egms-logo-box svg { width:62px; height:62px; display:block; }
        .egms-hero-body { padding:28px 30px 26px; }
        .egms-label { color:#9aa8ba; font-size:11px; font-weight:900; letter-spacing:.15em; text-transform:uppercase; }
        .egms-hero h1 { margin:7px 0 8px!important; color:#fff!important; font-size:clamp(27px,4vw,36px)!important; line-height:1.15!important; letter-spacing:-.025em; }
        .egms-hero p { margin:0!important; color:#9eacbe!important; font-size:16px!important; line-height:1.55!important; }
        .egms-tags { display:flex; flex-wrap:wrap; gap:8px; margin-top:19px; }
        .egms-tag { display:inline-flex; align-items:center; gap:7px; padding:8px 11px; border:1px solid #2b394b; border-radius:999px; color:#a2afbf; font-size:12px; }
        .egms-check { width:15px; height:15px; display:grid; place-items:center; border-radius:50%; color:#06140b; font-size:9px; font-weight:950; background:var(--green); }

        .egms-notice { margin:15px 0 18px; padding:16px 19px; border-left:4px solid var(--green); border-radius:12px; color:#a9bdaf; font-size:14px; line-height:1.55; background:linear-gradient(90deg,rgba(20,76,47,.60),rgba(17,45,32,.78)); }
        .egms-notice strong { color:#fff; }

        .egms-section { margin-top:11px; overflow:hidden; border:1px solid #253547; border-radius:14px; background:rgba(13,21,27,.96); transition:.2s ease; }
        .egms-section[open] { border-color:rgba(30,215,96,.58); box-shadow:0 15px 34px rgba(0,0,0,.18); }
        .egms-section summary { position:relative; display:flex; align-items:center; gap:13px; padding:18px 52px 18px 20px; color:#fff; font-size:16px; font-weight:850; cursor:pointer; list-style:none; }
        .egms-section summary::-webkit-details-marker { display:none; }
        .egms-section summary:after { content:"+"; position:absolute; right:20px; top:50%; transform:translateY(-50%); color:#718096; font-size:23px; }
        .egms-section[open] summary:after { content:"−"; color:var(--green2); }
        .egms-device { width:31px; color:var(--green2); font-size:20px; text-align:center; }
        .egms-content { padding:5px 24px 25px; border-top:1px solid #202e3c; }
        .egms-content p { color:#a7b3c2!important; font-size:15px!important; line-height:1.65!important; }
        .egms-content h3 { margin:22px 0 8px!important; color:#fff!important; font-size:18px!important; }
        .egms-content ol { margin:18px 0 4px; padding-left:23px; }
        .egms-content li { margin:10px 0; padding-left:4px; color:#b5bfcc; font-size:15px; line-height:1.55; }
        .egms-content li::marker { color:var(--green2); font-weight:900; }
        .egms-button { display:inline-flex; align-items:center; gap:8px; margin:11px 0 5px; padding:12px 17px; border-radius:10px; color:#06140b!important; font-size:14px; font-weight:900; text-decoration:none!important; background:linear-gradient(135deg,#57eb8c,#1ed760); transition:.2s ease; }
        .egms-button:hover { transform:translateY(-2px); box-shadow:0 12px 26px rgba(30,215,96,.20); }
        .egms-featured { margin:15px 0 20px; padding:19px; border:1px solid #31513f; border-radius:14px; background:linear-gradient(135deg,#10271b,#0d1c15); }
        .egms-featured-head { display:flex; align-items:center; gap:12px; margin-bottom:12px; }
        .egms-number { width:35px; height:35px; display:grid; place-items:center; flex:0 0 auto; border-radius:11px; color:#06130a; font-size:15px; font-weight:950; background:var(--green); }
        .egms-featured h3 { margin:0!important; }
        .egms-badge { display:inline-block; margin-left:7px; padding:4px 7px; border-radius:999px; color:#b9f7cf; font-size:10px; font-weight:900; text-transform:uppercase; background:#184e2d; }
        .egms-codebox { margin:13px 0; padding:15px; border:1px solid #327049; border-radius:11px; color:#a8b9ad; text-align:center; background:#0a1d12; }
        .egms-codebox strong { display:block; margin-top:4px; color:#fff; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:clamp(25px,5vw,38px); letter-spacing:.08em; }
        .egms-credential { margin:12px 0; padding:12px 14px; border:1px solid #344658; border-radius:10px; color:#aeb9c7; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:13px; background:#101a23; }
        .egms-credential span { color:var(--green2); font-weight:900; }
        .egms-link { color:var(--green2)!important; font-weight:850; text-decoration:none!important; }
        .egms-link:hover { text-decoration:underline!important; }
        .egms-warning { margin:15px 0 4px; padding:15px 17px; border:1px solid #4b4931; border-radius:11px; color:#c8c3a1; font-size:14px; line-height:1.6; background:#252312; }
        .egms-warning strong { color:#f0e78e; }

        @media(max-width:760px){
            .egms-page{padding-top:18px}.egms-shell{width:min(100% - 26px,540px)}.egms-hero{grid-template-columns:1fr}.egms-logo{min-height:132px}.egms-logo-box{width:84px;height:84px}.egms-logo-box svg{width:53px;height:53px}.egms-hero-body{padding:22px 19px}.egms-hero h1{font-size:27px!important}
        }
        @media(max-width:460px){.egms-section summary{padding:17px 46px 17px 16px;font-size:15px}.egms-content{padding:4px 18px 21px}.egms-featured{padding:15px}.egms-badge{display:block;width:max-content;margin:5px 0 0}}
        @media(prefers-reduced-motion:reduce){.egms-back,.egms-button,.egms-section{transition:none}}
    </style>

    <main class="egms-page" aria-labelledby="egms-title">
        <div class="egms-shell">
            <a class="egms-back" href="<?php echo esc_url( home_url( '/' ) ); ?>">← Centro de Apps</a>

            <section class="egms-hero">
                <div class="egms-logo" aria-hidden="true">
                    <div class="egms-logo-box">
                        <svg viewBox="0 0 64 64" role="img" aria-label="Spotify"><circle cx="32" cy="32" r="31" fill="#1ed760"/><path d="M17 25c11-3 23-2 33 3" fill="none" stroke="#07130b" stroke-width="5" stroke-linecap="round"/><path d="M19 34c9-2 19-1 28 3" fill="none" stroke="#07130b" stroke-width="4.4" stroke-linecap="round"/><path d="M21 42c7-1.4 15-.7 22 2" fill="none" stroke="#07130b" stroke-width="3.8" stroke-linecap="round"/></svg>
                    </div>
                </div>
                <div class="egms-hero-body">
                    <span class="egms-label">Guía oficial</span>
                    <h1 id="egms-title">Guía Completa de Activación Spotify+</h1>
                    <p>Descarga la app, ingresa tu código, inicia sesión con Spotify y tendrás acceso a todo.</p>
                    <div class="egms-tags" aria-label="Características"><span class="egms-tag"><span class="egms-check">✓</span> Activación rápida</span><span class="egms-tag"><span class="egms-check">✓</span> Descarga local</span><span class="egms-tag"><span class="egms-check">✓</span> Android, Android TV y Windows</span></div>
                </div>
            </section>

            <div class="egms-notice"><strong>Recomendación:</strong> sigue atentamente estos pasos para una activación exitosa de tu cuenta.</div>

            <details class="egms-section">
                <summary><span class="egms-device" aria-hidden="true">●</span>Android</summary>
                <div class="egms-content">
                    <p>Instala Spotify+ desde el enlace proporcionado, ingresa tu código e inicia sesión con Spotify.</p>
                    <a class="egms-button" href="<?php echo esc_url( $android_url ); ?>" download>↓ Descargar APP</a>
                    <ol><li>Descarga e instala la aplicación.</li><li>Abre Spotify+.</li><li>Ingresa el código de activación que te proporcionaron.</li><li>Inicia sesión con tu cuenta de Spotify.</li><li>Listo: ya tienes acceso al servicio.</li></ol>
                    <div class="egms-credential"><span>Código:</span> [Tu código]</div>
                </div>
            </details>

            <details class="egms-section">
                <summary><span class="egms-device" aria-hidden="true">▭</span>Android TV / Google TV / Fire TV</summary>
                <div class="egms-content">
                    <div class="egms-featured">
                        <div class="egms-featured-head"><span class="egms-number">1</span><h3>Downloader <span class="egms-badge">Recomendado</span></h3></div>
                        <div class="egms-codebox">Código Downloader<strong>6736378</strong></div>
                        <ol><li>Abre la aplicación <strong>Downloader</strong> en tu TV.</li><li>Ingresa el código <strong>6736378</strong>.</li><li>Descarga e instala Spotify+.</li><li>Abre la aplicación e ingresa tu código de activación.</li><li>Inicia sesión con tu cuenta de Spotify.</li><li>Listo: ya tienes acceso al servicio.</li></ol>
                        <div class="egms-credential"><span>URL corta:</span> <a class="egms-link" href="<?php echo esc_url( $downloader_url ); ?>" target="_blank" rel="noopener noreferrer">aftv.news/6736378</a></div>
                    </div>
                    <h3>Descarga directa</h3>
                    <a class="egms-button" href="<?php echo esc_url( $android_url ); ?>" download>↓ Descargar APP</a>
                    <ol><li>Descarga e instala la aplicación.</li><li>Abre Spotify+.</li><li>Ingresa el código de activación.</li><li>Inicia sesión con tu cuenta de Spotify.</li><li>Listo: ya tienes acceso al servicio.</li></ol>
                    <div class="egms-credential"><span>Código:</span> [Tu código]</div>
                </div>
            </details>

            <details class="egms-section">
                <summary><span class="egms-device" aria-hidden="true">⊞</span>Windows</summary>
                <div class="egms-content">
                    <p>Instala Spotify+ en tu computadora, ingresa tu código e inicia sesión con Spotify.</p>
                    <a class="egms-button" href="<?php echo esc_url( $windows_url ); ?>" download>↓ Descargar APP</a>
                    <ol><li>Descarga el instalador.</li><li>Abre el archivo <strong>SpotifyPlus-setup.exe</strong>.</li><li>Ingresa el código de activación que te proporcionaron.</li><li>Inicia sesión con tu cuenta de Spotify.</li><li>Listo: ya tienes acceso al servicio.</li></ol>
                    <div class="egms-credential"><span>Código:</span> [Tu código]</div>

                    <h3>Si Windows muestra “Windows protegió tu PC”</h3>
                    <div class="egms-warning"><strong>Importante:</strong> continúa únicamente si descargaste el instalador desde el enlace indicado y reconoces su procedencia. Si tienes dudas, no lo ejecutes y consulta primero con tu proveedor.</div>
                    <ol><li>En la advertencia, selecciona <strong>Más información</strong>.</li><li>Si verificaste el origen del archivo, selecciona <strong>Ejecutar de todas formas</strong>.</li><li>Continúa la instalación normalmente.</li></ol>
                    <div class="egms-warning"><strong>Si Chrome o Edge bloquea la descarga:</strong> revisa el aviso del navegador y conserva el archivo solamente después de confirmar que la dirección de descarga coincide con el enlace proporcionado.</div>
                </div>
            </details>
        </div>
    </main>
    <?php
    return ob_get_clean();
} );
