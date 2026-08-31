/**
 * El Gamer MX — Catálogo de canales Emby/Jellyfin
 * Code Snippets: PHP / Run everywhere / Priority 10.
 * La página /channels/ debe contener únicamente: [egm_channels]
 */

if ( ! defined( 'ABSPATH' ) ) { exit; }

add_shortcode( 'egm_channels', function () {
    $data_url  = 'https://apps.multiplataforma.co/channels/channels_data.json';
    $logo_base = 'https://apps.multiplataforma.co/channels/';
    $cache_key = 'egm_channels_catalog_v1';
    $catalog   = get_transient( $cache_key );

    if ( false === $catalog ) {
        $response = wp_remote_get( $data_url, array( 'timeout' => 15, 'redirection' => 3 ) );
        if ( ! is_wp_error( $response ) && 200 === wp_remote_retrieve_response_code( $response ) ) {
            $decoded = json_decode( wp_remote_retrieve_body( $response ), true );
            if ( is_array( $decoded ) ) {
                $catalog = $decoded;
                set_transient( $cache_key, $catalog, 12 * HOUR_IN_SECONDS );
            }
        }
    }

    if ( ! is_array( $catalog ) ) { $catalog = array(); }
    $total = 0;
    foreach ( $catalog as $category ) { $total += isset( $category['channels'] ) && is_array( $category['channels'] ) ? count( $category['channels'] ) : 0; }

    $emby_icon = 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/Captura-de-pantalla-2026-08-20-a-las-12.03.16-a.m.png';
    $jelly_icon = 'https://apps.elgamermexicano.com/wp-content/uploads/2026/08/Captura-de-pantalla-2026-08-20-a-las-12.03.03-a.m.png';

    ob_start(); ?>
    <style>
      html,body{margin:0!important;background:#06090e!important}body:has(.egmc-page) header.wp-block-template-part,body:has(.egmc-page) footer.wp-block-template-part,body:has(.egmc-page) .entry-title,body:has(.egmc-page) .wp-block-post-title{display:none!important}body:has(.egmc-page) .wp-site-blocks,body:has(.egmc-page) main,body:has(.egmc-page) .entry-content,body:has(.egmc-page) .wp-block-post-content{width:100%!important;max-width:none!important;margin:0!important;padding:0!important;background:transparent!important}
      .egmc-page,.egmc-page *{box-sizing:border-box}.egmc-page{--accent:#7d88ff;--panel:#0d141c;--line:#273448;--text:#f6f8fc;--muted:#96a4b7;min-height:100vh;padding:28px 0 80px;color:var(--text);font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:radial-gradient(circle at 50% -180px,rgba(110,82,255,.14),transparent 34rem),linear-gradient(180deg,#080c13,#05070b)}.egmc-shell{width:min(1120px,calc(100% - 40px));margin:0 auto}.egmc-back{display:inline-flex;margin-bottom:24px;color:#9dabbf!important;font-size:14px;font-weight:800;text-decoration:none!important}.egmc-hero small{color:#8a91ff;font-size:11px;font-weight:900;letter-spacing:.16em;text-transform:uppercase}.egmc-hero h1{margin:8px 0 8px!important;color:#fff!important;font-size:clamp(38px,6vw,56px)!important;line-height:1!important;letter-spacing:-.04em}.egmc-hero p{margin:0!important;color:#9aa8bb!important;font-size:17px!important}.egmc-services{display:flex;gap:9px;margin-top:18px}.egmc-service{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid #2a3749;border-radius:999px;color:#a8b4c4;font-size:12px;background:#0c121a}.egmc-service img{width:22px!important;height:22px!important;object-fit:contain!important;border-radius:6px;background:#fff}.egmc-controls{position:sticky;top:0;z-index:8;margin:32px 0 18px;padding:15px 0;background:rgba(6,9,14,.92);backdrop-filter:blur(14px)}.egmc-search{width:100%;padding:15px 18px;border:1px solid #2a384c;border-radius:14px;outline:0;color:#fff;font:inherit;background:#0d141c}.egmc-search:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(125,136,255,.12)}.egmc-filters{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.egmc-filter{padding:8px 12px;border:1px solid #2b394b;border-radius:999px;color:#9eacbf;font-size:12px;font-weight:750;cursor:pointer;background:#0d141c}.egmc-filter.active,.egmc-filter:hover{border-color:var(--accent);color:#c8ccff;background:rgba(125,136,255,.12)}.egmc-stats{display:grid;grid-template-columns:repeat(3,1fr);margin-bottom:18px;border:1px solid #29364a;border-radius:14px;background:#0d141c}.egmc-stat{padding:17px;text-align:center}.egmc-stat strong{display:block;color:#8e97ff;font-size:24px}.egmc-stat span{color:#8391a4;font-size:11px}.egmc-category{margin-top:14px;overflow:hidden;border:1px solid #29364a;border-radius:17px;background:#0d141c}.egmc-cat-head{display:flex;align-items:center;gap:12px;padding:17px 19px;border-bottom:1px solid #243145}.egmc-cat-icon{width:36px;height:36px;display:grid;place-items:center;border-radius:10px;color:#d5d8ff;background:rgba(125,136,255,.16)}.egmc-cat-head h2{margin:0!important;color:#fff!important;font-size:17px!important}.egmc-cat-count{margin-left:auto;padding:6px 9px;border-radius:999px;color:#aeb4ff;font-size:10px;font-weight:900;background:rgba(125,136,255,.14)}.egmc-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:9px;padding:14px}.egmc-channel{min-width:0;padding:12px 8px;border:1px solid #263447;border-radius:11px;text-align:center;background:#101720}.egmc-channel img{width:52px!important;height:52px!important;display:block!important;margin:0 auto 9px!important;padding:4px;object-fit:contain!important;border-radius:9px;background:#fff}.egmc-channel span{display:block;overflow:hidden;color:#a9b5c4;font-size:9px;font-weight:750;line-height:1.3;text-overflow:ellipsis}.egmc-empty{display:none;padding:45px 20px;text-align:center;color:#8997aa}.egmc-empty.show{display:block}
      @media(max-width:900px){.egmc-grid{grid-template-columns:repeat(5,minmax(0,1fr))}}@media(max-width:650px){.egmc-shell{width:min(100% - 24px,520px)}.egmc-grid{grid-template-columns:repeat(3,minmax(0,1fr));padding:10px}.egmc-controls{top:0}.egmc-stats{grid-template-columns:repeat(3,1fr)}.egmc-stat{padding:13px 6px}.egmc-stat strong{font-size:20px}}@media(max-width:380px){.egmc-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
    </style>
    <main class="egmc-page" id="egmc-catalog">
      <div class="egmc-shell">
        <a class="egmc-back" href="<?php echo esc_url( home_url( '/jellyfin/' ) ); ?>">← Volver a Jellyfin</a>
        <header class="egmc-hero"><small>Catálogo</small><h1>Canales disponibles</h1><p>Busca y filtra los canales disponibles para Emby y Jellyfin.</p><div class="egmc-services"><span class="egmc-service"><img src="<?php echo esc_url( $emby_icon ); ?>" alt="">Emby</span><span class="egmc-service"><img src="<?php echo esc_url( $jelly_icon ); ?>" alt="">Jellyfin</span></div></header>
        <?php if ( empty( $catalog ) ) : ?><div class="egmc-empty show">No fue posible cargar el catálogo. Recarga la página en unos minutos.</div><?php else : ?>
        <div class="egmc-controls"><input class="egmc-search" id="egmc-search" type="search" placeholder="Buscar canal…" aria-label="Buscar canal"><div class="egmc-filters" id="egmc-filters"><button class="egmc-filter active" type="button" data-category="all">Todos</button><?php foreach($catalog as $i=>$category): ?><button class="egmc-filter" type="button" data-category="c<?php echo (int)$i; ?>"><?php echo esc_html($category['name']); ?></button><?php endforeach; ?></div></div>
        <div class="egmc-stats"><div class="egmc-stat"><strong><?php echo (int)$total; ?></strong><span>Canales totales</span></div><div class="egmc-stat"><strong><?php echo (int)count($catalog); ?></strong><span>Categorías</span></div><div class="egmc-stat"><strong id="egmc-visible"><?php echo (int)$total; ?></strong><span>Visibles</span></div></div>
        <div id="egmc-groups">
          <?php foreach($catalog as $i=>$category): ?><section class="egmc-category" data-category="c<?php echo (int)$i; ?>"><div class="egmc-cat-head"><span class="egmc-cat-icon">●</span><h2><?php echo esc_html($category['name']); ?></h2><span class="egmc-cat-count"><b class="egmc-local-count"><?php echo isset($category['channels'])?count($category['channels']):0; ?></b> canales</span></div><div class="egmc-grid">
          <?php foreach(($category['channels']??array()) as $channel): $logo=isset($channel['logo'])?esc_url($logo_base.ltrim($channel['logo'],'/')):''; ?><article class="egmc-channel" data-name="<?php echo esc_attr(strtolower(remove_accents($channel['name']??''))); ?>"><img src="<?php echo $logo; ?>" alt="<?php echo esc_attr($channel['alt']??$channel['name']??''); ?>" loading="lazy" decoding="async" onerror="this.onerror=null;this.src='<?php echo esc_url($jelly_icon); ?>';"><span title="<?php echo esc_attr($channel['name']??''); ?>"><?php echo esc_html($channel['name']??''); ?></span></article><?php endforeach; ?>
          </div></section><?php endforeach; ?>
        </div><div class="egmc-empty" id="egmc-empty">No se encontraron canales. Prueba con otro término o selecciona otra categoría.</div>
        <script>(function(){const root=document.getElementById('egmc-catalog');if(!root)return;const input=root.querySelector('#egmc-search'),buttons=[...root.querySelectorAll('.egmc-filter')],groups=[...root.querySelectorAll('.egmc-category')],visible=root.querySelector('#egmc-visible'),empty=root.querySelector('#egmc-empty');let active='all';function norm(s){return(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()}function render(){const q=norm(input.value);let total=0;groups.forEach(g=>{const allowed=active==='all'||g.dataset.category===active;let local=0;g.querySelectorAll('.egmc-channel').forEach(c=>{const show=allowed&&(!q||c.dataset.name.includes(q));c.hidden=!show;if(show){local++;total++}});g.hidden=local===0;const n=g.querySelector('.egmc-local-count');if(n)n.textContent=local});visible.textContent=total;empty.classList.toggle('show',total===0)}buttons.forEach(b=>b.addEventListener('click',()=>{buttons.forEach(x=>x.classList.remove('active'));b.classList.add('active');active=b.dataset.category;render()}));input.addEventListener('input',render)})();</script>
        <?php endif; ?>
      </div>
    </main>
    <?php return ob_get_clean();
} );
