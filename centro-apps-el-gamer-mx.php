/**
 * El Gamer MX — Centro de Apps
 * Code Snippets: PHP / Run everywhere / Priority 10.
 * La portada debe contener únicamente: [egm_apps]
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_shortcode( 'egm_apps', function () {
    $base = home_url( '/' );
    $logo = 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/WhatsApp-Image-2026-08-22-at-17.47.05.jpeg';
    $yt_icon = 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/youtubeplus.png';

    $apps = array(
        array( 'slug' => 'youtube-plus', 'class' => 'youtube', 'eyebrow' => 'Guía de instalación', 'name' => 'YouTube+', 'description' => 'Instala, activa y disfruta en Android, TV y Windows.', 'icon' => $yt_icon, 'initials' => 'YT+' ),
        array( 'slug' => 'iptv', 'class' => 'iptv', 'eyebrow' => 'Configuración', 'name' => 'IPTV', 'description' => 'Apps recomendadas, instalación y configuración de acceso.', 'icon' => 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/Captura-de-pantalla-2026-08-20-a-las-12.03.29-a.m.png', 'initials' => 'TV' ),
        array( 'slug' => 'ibo-pro', 'class' => 'ibo', 'eyebrow' => 'Activación', 'name' => 'IBO Pro Player', 'description' => 'Instalación, activación y configuración paso a paso.', 'icon' => 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/ibo.png', 'initials' => 'IBO' ),
        array( 'slug' => 'plex', 'class' => 'plex', 'eyebrow' => 'Guía de configuración', 'name' => 'Plex', 'description' => 'Configura tu biblioteca en Smart TV, celular, computadora y web.', 'icon' => 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/Captura-de-pantalla-2026-08-20-a-las-12.02.48-a.m.png', 'initials' => 'P' ),
        array( 'slug' => 'emby', 'class' => 'emby', 'eyebrow' => 'Guía de instalación', 'name' => 'Emby', 'description' => 'Instalación, acceso y configuración multiplataforma.', 'icon' => 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/Captura-de-pantalla-2026-08-20-a-las-12.03.16-a.m.png', 'initials' => 'E' ),
        array( 'slug' => 'jellyfin', 'class' => 'jellyfin', 'eyebrow' => 'Guía de configuración', 'name' => 'Jellyfin', 'description' => 'Configuración por dispositivo y acceso al servicio.', 'icon' => 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/Captura-de-pantalla-2026-08-20-a-las-12.03.03-a.m.png', 'initials' => 'J' ),
        array( 'slug' => 'spotify', 'class' => 'spotify', 'eyebrow' => 'Guía de instalación', 'name' => 'Spotify+', 'description' => 'Android, Windows y activación con código.', 'initials' => 'S' ),
        array( 'slug' => 'channels', 'class' => 'channels', 'eyebrow' => 'Catálogo', 'name' => 'Canales', 'description' => 'Catálogo completo de canales para Emby y Jellyfin.', 'icon' => 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/Captura-de-pantalla-2026-08-20-a-las-12.03.39-a.m.png', 'initials' => 'TV' ),
    );

    ob_start();
    ?>
    <style>
        html, body { margin: 0 !important; background: #05070b !important; }
        body:has(.egmx-portal) header.wp-block-template-part,
        body:has(.egmx-portal) footer.wp-block-template-part,
        body:has(.egmx-portal) .entry-title,
        body:has(.egmx-portal) .wp-block-post-title { display: none !important; }
        body:has(.egmx-portal) .wp-site-blocks,
        body:has(.egmx-portal) main,
        body:has(.egmx-portal) .entry-content,
        body:has(.egmx-portal) .wp-block-post-content { width: 100% !important; max-width: none !important; margin: 0 !important; padding: 0 !important; background: transparent !important; }

        .egmx-portal, .egmx-portal * { box-sizing: border-box; }
        .egmx-portal {
            --red: #ff3344; --red2: #bd1026; --panel: #0d131c; --panel2: #111a26;
            --line: #243144; --text: #f7f9fc; --muted: #9aa8ba;
            position: relative; isolation: isolate; min-height: 100vh; overflow: hidden;
            color: var(--text); font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background:
                radial-gradient(circle at 84% 4%, rgba(255,51,68,.14), transparent 27rem),
                radial-gradient(circle at -8% 42%, rgba(132,19,35,.17), transparent 30rem),
                linear-gradient(180deg, #080b11 0%, #05070b 100%);
        }
        .egmx-portal:before { content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none; opacity: .24; background-image: linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px); background-size: 48px 48px; mask-image: linear-gradient(to bottom, black, transparent 65%); }
        .egmx-shell { width: min(1370px, calc(100% - 48px)); margin: 0 auto; padding: 18px 0 58px; }

        .egmx-hero { position: relative; display: flex; flex-direction: column-reverse; align-items: center; justify-content: flex-end; min-height: 382px; margin-bottom: 8px; padding: 8px 40px 26px; overflow: hidden; text-align: center; }
        .egmx-hero:before { content: ""; position: absolute; inset: 4px -9% 70px; z-index: -1; opacity: .82; background: radial-gradient(ellipse at center, rgba(255,30,47,.20), transparent 37%), repeating-radial-gradient(circle at 50% 4%, rgba(255,38,55,.34) 0 1px, transparent 1.5px 13px); mask-image: linear-gradient(90deg, transparent, #000 17%, #000 83%, transparent); }
        .egmx-hero:after { content: ""; position: absolute; left: -8%; right: -8%; bottom: 64px; height: 155px; z-index: -1; border-bottom: 2px solid rgba(255,38,55,.85); background: linear-gradient(165deg, transparent 0 35%, rgba(255,31,48,.11) 36% 45%, transparent 46%), linear-gradient(195deg, transparent 0 35%, rgba(255,31,48,.11) 36% 45%, transparent 46%); clip-path: polygon(0 48%, 23% 76%, 35% 46%, 43% 92%, 50% 68%, 57% 92%, 65% 46%, 77% 76%, 100% 48%, 100% 100%, 0 100%); }
        .egmx-brand { position: relative; z-index: 2; }
        .egmx-kicker { display: none; }
        .egmx-hero h1 { margin: 4px 0 18px !important; color: #fff !important; font-size: clamp(46px, 5.2vw, 68px) !important; line-height: 1 !important; letter-spacing: -.045em; font-weight: 900 !important; text-shadow: 0 8px 28px rgba(0,0,0,.48); }
        .egmx-hero h1 span { color: #fff; }
        .egmx-hero h1:after { content: ""; display: block; width: 176px; height: 3px; margin: 13px auto -3px; border-radius: 99px; background: linear-gradient(90deg, transparent, var(--red), transparent); box-shadow: 0 0 16px rgba(255,51,68,.55); }
        .egmx-hero p { max-width: 760px; margin: 0 auto !important; color: #a9b5c5 !important; font-size: 18px !important; line-height: 1.55 !important; }
        .egmx-logo-stage { position: relative; z-index: 2; display: grid; place-items: center; min-height: 238px; }
        .egmx-logo-ring { width: 238px; height: 238px; display: grid; place-items: center; padding: 10px; border: 2px solid #ff2637; border-radius: 50%; background: #07090d; box-shadow: 0 0 0 8px rgba(255,38,55,.10), 0 0 42px rgba(255,24,44,.26), 0 25px 60px rgba(0,0,0,.44); }
        .egmx-logo-ring img { width: 212px !important; height: 212px !important; object-fit: contain !important; display: block !important; border-radius: 50%; mix-blend-mode: screen; filter: contrast(1.18); }

        .egmx-toolbar { display: none; }
        .egmx-toolbar small { color: #ff6673; font-size: 11px; font-weight: 900; letter-spacing: .16em; text-transform: uppercase; }
        .egmx-toolbar h2 { margin: 7px 0 0 !important; color: #fff !important; font-size: 28px !important; letter-spacing: -.025em; }
        .egmx-count { padding: 9px 13px; border: 1px solid var(--line); border-radius: 999px; color: #8f9caf; font-size: 12px; font-weight: 800; background: #0b1119; }

        .egmx-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 18px; }
        .egmx-card { --accent: #ff4655; --glow: rgba(255,70,85,.22); position: relative; min-width: 0; min-height: 220px; display: grid !important; grid-template-columns: 96px minmax(0,1fr); align-items: start; column-gap: 22px; overflow: hidden; padding: 30px 28px; border: 1px solid var(--line); border-radius: 18px; color: inherit !important; text-decoration: none !important; background: linear-gradient(125deg, color-mix(in srgb, var(--accent) 15%, #101720), rgba(9,14,22,.98) 76%); box-shadow: 0 14px 34px rgba(0,0,0,.17); transition: transform .28s ease, border-color .28s ease, box-shadow .28s ease; }
        .egmx-card:before { content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .9; background: radial-gradient(circle at 92% 0%, var(--glow), transparent 38%); }
        .egmx-card:hover { transform: translateY(-7px); border-color: color-mix(in srgb, var(--accent) 60%, #344154); box-shadow: 0 24px 55px rgba(0,0,0,.30), 0 0 28px var(--glow); }
        .egmx-card:focus-visible { outline: 3px solid #fff; outline-offset: 3px; }
        .egmx-card.iptv { --accent:#38a8ff; --glow:rgba(56,168,255,.18); }
        .egmx-card.ibo { --accent:#ad77ff; --glow:rgba(173,119,255,.18); }
        .egmx-card.plex { --accent:#e5aa19; --glow:rgba(229,170,25,.17); }
        .egmx-card.emby { --accent:#31d87b; --glow:rgba(49,216,123,.17); }
        .egmx-card.jellyfin { --accent:#9c7bff; --glow:rgba(156,123,255,.18); }
        .egmx-card.spotify { --accent:#1ed760; --glow:rgba(30,215,96,.18); }
        .egmx-card.channels { --accent:#7d88ff; --glow:rgba(125,136,255,.18); }
        .egmx-card-top { position: static; z-index: 1; display: flex; align-items: flex-start; justify-content: space-between; }
        .egmx-icon { width: 88px; height: 88px; display: grid; place-items: center; overflow: hidden; border: 1px solid rgba(255,255,255,.50); border-radius: 17px; color: #0b1220; font-size: 20px; font-weight: 950; background: linear-gradient(145deg, #fff, #eef1f5); box-shadow: 0 13px 28px rgba(0,0,0,.20); }
        .egmx-icon img { width: 100% !important; height: 100% !important; object-fit: cover !important; display: block !important; }
        .egmx-card.plex .egmx-icon img,
        .egmx-card.iptv .egmx-icon img,
        .egmx-card.ibo .egmx-icon img,
        .egmx-card.emby .egmx-icon img,
        .egmx-card.jellyfin .egmx-icon img,
        .egmx-card.channels .egmx-icon img { padding: 5px; object-fit: contain !important; background: #fff; }
        .egmx-card.spotify .egmx-icon { background: #fff; }
        .egmx-card.spotify .egmx-icon svg { width: 55px; height: 55px; display: block; }
        .egmx-arrow { position: absolute; left: 138px; bottom: 26px; width: auto; height: auto; display: block; border: 0; color: var(--accent); font-size: 0; font-weight: 900; transition: .25s ease; }
        .egmx-arrow:before { content: "Ver tutorial →"; font-size: 14px; }
        .egmx-card:hover .egmx-arrow { color: var(--accent); background: transparent; transform: translateX(4px); }
        .egmx-meta { position: relative; z-index: 1; padding-bottom: 42px; }
        .egmx-meta small { display: block; margin-bottom: 8px; color: var(--accent); font-size: 10px; font-weight: 950; letter-spacing: .14em; text-transform: uppercase; }
        .egmx-meta h3 { margin: 0 0 9px !important; color: #fff !important; font-size: 22px !important; line-height: 1.2 !important; }
        .egmx-meta p { min-height: 48px; margin: 0 !important; color: #b4bfcd !important; font-size: 14px !important; line-height: 1.55 !important; }

        .egmx-recommend { position: relative; width: min(820px, 100%); display: grid; grid-template-columns: 52px 1fr; align-items: center; gap: 18px; margin: 18px auto 0; padding: 18px 24px; overflow: hidden; border: 1px solid #263347; border-radius: 15px; background: rgba(10,15,23,.92); }
        .egmx-recommend:after { content: ""; position: absolute; right: -50px; width: 220px; height: 220px; border-radius: 50%; background: rgba(255,51,68,.11); filter: blur(12px); }
        .egmx-rec-icon { width: 52px; height: 52px; display: grid; place-items: center; border-radius: 15px; color: #fff; font-size: 24px; background: linear-gradient(145deg, #ff4b5b, #b80e25); box-shadow: 0 12px 30px rgba(255,51,68,.22); }
        .egmx-recommend h3 { margin: 0 0 4px !important; color: #fff !important; font-size: 18px !important; }
        .egmx-recommend p { margin: 0 !important; color: #a5b0bf !important; font-size: 14px !important; }
        .egmx-wa { position: absolute; inset: 0; z-index: 3; display: block; overflow: hidden; color: transparent !important; font-size: 0; text-decoration: none !important; background: transparent; }
        .egmx-wa:hover { transform: translateY(-2px); box-shadow: 0 12px 26px rgba(37,211,102,.20); }

        @media (max-width: 920px) {
            .egmx-shell { width: min(100% - 32px, 760px); padding-top: 28px; }
            .egmx-hero { min-height: 360px; padding: 8px 24px 26px; }
            .egmx-logo-ring { width: 205px; height: 205px; }
            .egmx-logo-ring img { width: 182px !important; height: 182px !important; }
            .egmx-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
        }
        @media (max-width: 620px) {
            .egmx-shell { width: min(100% - 24px, 460px); padding: 12px 0 50px; }
            .egmx-hero { gap: 8px; min-height: auto; padding: 16px 12px 24px; }
            .egmx-hero h1 { font-size: clamp(40px, 14vw, 54px) !important; }
            .egmx-hero p { font-size: 16px !important; }
            .egmx-logo-stage { min-height: 174px; }
            .egmx-logo-ring { width: 164px; height: 164px; }
            .egmx-logo-ring img { width: 144px !important; height: 144px !important; }
            .egmx-toolbar { margin-top: 30px; }
            .egmx-toolbar h2 { font-size: 24px !important; }
            .egmx-count { display: none; }
            .egmx-grid { grid-template-columns: 1fr; gap: 14px; }
            .egmx-card { min-height: 210px; grid-template-columns: 76px minmax(0,1fr); column-gap: 17px; padding: 24px 20px; }
            .egmx-icon { width: 72px; height: 72px; border-radius: 15px; }
            .egmx-arrow { left: 113px; bottom: 22px; }
            .egmx-meta p { min-height: 0; }
            .egmx-recommend { grid-template-columns: 48px 1fr; padding: 17px; }
            .egmx-rec-icon { width: 48px; height: 48px; }
            .egmx-wa { margin: 0; }
        }
        @media (prefers-reduced-motion: reduce) { .egmx-card, .egmx-arrow, .egmx-wa { transition: none; } }
    </style>

    <main class="egmx-portal" aria-labelledby="egmx-title">
        <div class="egmx-shell">
            <section class="egmx-hero" aria-label="Centro de Apps El Gamer MX">
                <div class="egmx-brand">
                    <div class="egmx-kicker">El Gamer MX</div>
                    <h1 id="egmx-title">Centro de <span>Apps</span></h1>
                    <p>Todo lo que necesitas para instalar, configurar y activar tus servicios, reunido en un solo lugar.</p>
                </div>
                <div class="egmx-logo-stage" aria-hidden="true">
                    <div class="egmx-logo-ring"><img src="<?php echo esc_url( $logo ); ?>" alt="" loading="eager" decoding="async"></div>
                </div>
            </section>

            <div class="egmx-toolbar">
                <div><small>Biblioteca de soporte</small><h2>Selecciona una aplicación</h2></div>
                <span class="egmx-count">8 recursos disponibles</span>
            </div>

            <section class="egmx-grid" aria-label="Guías de aplicaciones">
                <?php foreach ( $apps as $app ) : ?>
                    <a class="egmx-card <?php echo esc_attr( $app['class'] ); ?>" href="<?php echo esc_url( home_url( '/' . $app['slug'] . '/' ) ); ?>">
                        <div class="egmx-card-top">
                            <div class="egmx-icon">
                                <?php if ( ! empty( $app['icon'] ) ) : ?>
                                    <img src="<?php echo esc_url( $app['icon'] ); ?>" alt="" loading="lazy" decoding="async">
                                <?php elseif ( 'spotify' === $app['class'] ) : ?>
                                    <svg viewBox="0 0 64 64" role="img" aria-label="Spotify">
                                        <circle cx="32" cy="32" r="30" fill="#1ed760"/>
                                        <path d="M17 25.5c10.4-3 22.5-2.1 31.1 2.5" fill="none" stroke="#07120b" stroke-width="5" stroke-linecap="round"/>
                                        <path d="M19.5 34c8.9-2.3 18.7-1.5 26.1 2.2" fill="none" stroke="#07120b" stroke-width="4.2" stroke-linecap="round"/>
                                        <path d="M22 42c7-1.6 14.1-1 20.5 2" fill="none" stroke="#07120b" stroke-width="3.8" stroke-linecap="round"/>
                                    </svg>
                                <?php else : ?>
                                    <span aria-hidden="true"><?php echo esc_html( $app['initials'] ); ?></span>
                                <?php endif; ?>
                            </div>
                            <span class="egmx-arrow" aria-hidden="true">↗</span>
                        </div>
                        <div class="egmx-meta">
                            <small><?php echo esc_html( $app['eyebrow'] ); ?></small>
                            <h3><?php echo esc_html( $app['name'] ); ?></h3>
                            <p><?php echo esc_html( $app['description'] ); ?></p>
                        </div>
                    </a>
                <?php endforeach; ?>
            </section>

            <aside class="egmx-recommend" aria-label="Recomendación de soporte">
                <div class="egmx-rec-icon" aria-hidden="true">★</div>
                <div><h3>¿Es tu primera instalación?</h3><p>Empieza por la guía de tu app y sigue cada paso. Si algo no coincide, nuestro equipo puede ayudarte.</p></div>
                <a class="egmx-wa" href="https://wa.me/522229554736" target="_blank" rel="noopener noreferrer">Contactar soporte <span aria-hidden="true">→</span></a>
            </aside>
        </div>
    </main>
    <?php
    return ob_get_clean();
} );
