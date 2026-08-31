<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#080b10">
    <meta name="description" content="Consulta de correos y códigos de acceso de EL GAMER MX.">
    <title>Consultar correo | EL GAMER MX</title>
    <link rel="icon" type="image/png" href="/images/favicon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/styles/global_design.css?v=20260829codes1">
</head>
<body>
    <main class="page-shell">
        <header class="brand-header" aria-label="EL GAMER MX">
            <a class="brand-link" href="https://elgamermexicano.com" aria-label="Ir a EL GAMER MX">
                <img src="/images/logo/logo-horizontal.png" alt="EL GAMER MX · La revolución del entretenimiento" class="brand-logo">
            </a>
            <span class="secure-badge">
                <span class="secure-dot" aria-hidden="true"></span>
                Consulta segura
            </span>
        </header>

        <section class="consult-card" aria-labelledby="consult-title">
            <div class="accent-line" aria-hidden="true"><span></span><span></span><span></span></div>

            <div class="card-content">
                <div class="title-block">
                    <span class="eyebrow">PORTAL DE CÓDIGOS</span>
                    <h1 id="consult-title">Consulta tu correo</h1>
                    <p>Ingresa la dirección asignada a tu servicio para revisar los mensajes y códigos disponibles.</p>
                </div>

                <form action="inbox.php" method="get" class="consult-form">
                    <label for="email">Correo electrónico</label>
                    <div class="input-row">
                        <div class="input-wrap">
                            <span class="mail-icon" aria-hidden="true">
                                <svg viewBox="0 0 24 24" role="img"><path d="M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Zm0 2 8 5 8-5H4Zm16 10V9.4l-8 5-8-5V17h16Z"/></svg>
                            </span>
                            <input type="email" id="email" name="email" placeholder="nombre@dominio.com" autocomplete="email" inputmode="email" required maxlength="80">
                        </div>
                        <button type="submit">
                            Consultar bandeja
                            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m13 5 7 7-7 7-1.4-1.4 4.6-4.6H4v-2h12.2l-4.6-4.6L13 5Z"/></svg>
                        </button>
                    </div>
                </form>

                <div class="valid-domains" aria-labelledby="domains-title">
                    <div class="domain-heading">
                        <span class="info-icon" aria-hidden="true">i</span>
                        <div>
                            <h2 id="domains-title">Dominios disponibles</h2>
                            <p>La dirección debe terminar en uno de estos dominios:</p>
                        </div>
                    </div>
                    <ul>
                        <li>@elgamermexicano.com</li>
                        <li>@myplataformadigital.net</li>
                        <li>@vepquim.com</li>
                    </ul>
                </div>

                <div class="resultado-container" aria-live="polite">
                    <div class="resultado"></div>
                </div>
            </div>
        </section>

        <footer class="page-footer">
            <span>EL GAMER MX</span>
            <span class="footer-separator" aria-hidden="true">•</span>
            <span>La revolución del entretenimiento</span>
        </footer>
    </main>
</body>
</html>
