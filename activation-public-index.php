<?php
declare(strict_types=1);
$activationId = preg_replace('/[^a-z0-9-]/i', '', (string) ($_GET['id'] ?? ''));
$hasValidLink = $activationId !== '' && strlen($activationId) >= 20;
?>
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="theme-color" content="#080b10">
    <meta name="description" content="Vincula Netflix a tu televisión sin compartir contraseñas.">
    <title>Activar Netflix TV | EL GAMER MX</title>
    <link rel="icon" type="image/png" href="/images/favicon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/styles/activation-public.css?v=20260829p1">
</head>
<body>
<main class="public-shell">
    <header class="public-header">
        <img src="/images/logo-horizontal.png" alt="EL GAMER MX · La revolución del entretenimiento">
        <span class="secure-label"><i></i> Activación protegida</span>
    </header>

    <section class="activation-card">
        <div class="accent"><span></span><span></span><span></span></div>
        <div class="instructions">
            <div class="service-title"><span class="netflix-logo">N</span><div><small>NETFLIX TV VIP</small><strong>Conecta tu televisión</strong></div></div>
            <h1>Activa Netflix sin compartir la contraseña</h1>
            <p>Solo necesitas el código que aparece en la pantalla de tu TV. Este enlace está preparado para una activación segura.</p>
            <ol>
                <li><span>1</span><div><strong>Abre Netflix en tu TV</strong><small>Selecciona “Iniciar sesión”.</small></div></li>
                <li><span>2</span><div><strong>Elige usar un código</strong><small>Tu televisión mostrará 8 números.</small></div></li>
                <li><span>3</span><div><strong>Escríbelo en este portal</strong><small>La conexión se realizará automáticamente.</small></div></li>
            </ol>
        </div>

        <div class="activation-form-panel">
            <div class="form-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-6v2h2v2H8v-2h2v-2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Zm0 2v10h16V7H4Z"/></svg>
            </div>
            <span class="eyebrow">CÓDIGO DE TELEVISIÓN</span>
            <h2>Ingresa los 8 números</h2>
            <p>El código vence después de unos minutos. Si ya cambió, utiliza el nuevo que muestra tu TV.</p>

            <?php if ($hasValidLink): ?>
                <form id="linkForm" novalidate>
                    <label for="tvCode">Código de Netflix</label>
                    <input type="text" id="tvCode" name="tvCode" placeholder="00000000" inputmode="numeric" pattern="[0-9]{8}" minlength="8" maxlength="8" autocomplete="one-time-code" required>
                    <input type="hidden" id="idAcc" value="<?= htmlspecialchars($activationId, ENT_QUOTES, 'UTF-8') ?>">
                    <button type="submit" id="submitButton"><span>Vincular mi televisión</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m13 5 7 7-7 7-1.4-1.4 4.6-4.6H4v-2h12.2l-4.6-4.6L13 5Z"/></svg></button>
                </form>
                <div id="responseMessage" class="response" role="status" aria-live="polite"></div>
            <?php else: ?>
                <div class="response error visible"><strong>Este enlace no es válido</strong><span>Solicita un enlace nuevo a atención a clientes.</span></div>
            <?php endif; ?>

            <div class="privacy-note"><span>✓</span><p><strong>No solicitamos tu contraseña.</strong><br>El código conecta únicamente la televisión indicada.</p></div>
        </div>
    </section>

    <footer>¿Necesitas ayuda? <a href="https://wa.me/522229554736">222 955 4736</a> · <a href="https://elgamermexicano.com">elgamermexicano.com</a></footer>
</main>

<?php if ($hasValidLink): ?>
<script>
(function () {
    var form = document.getElementById('linkForm');
    var input = document.getElementById('tvCode');
    var button = document.getElementById('submitButton');
    var responseBox = document.getElementById('responseMessage');

    input.addEventListener('input', function () {
        input.value = input.value.replace(/\D/g, '').slice(0, 8);
        responseBox.className = 'response';
        responseBox.textContent = '';
    });

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        var tvCode = input.value.trim();
        if (!/^\d{8}$/.test(tvCode)) {
            showMessage('error', 'Código incompleto', 'Escribe los 8 números que aparecen en tu televisión.');
            input.focus();
            return;
        }

        button.disabled = true;
        button.classList.add('loading');
        button.querySelector('span').textContent = 'Conectando con Netflix…';
        responseBox.className = 'response';

        try {
            var request = await fetch('/vincular_tv.php', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
                body: JSON.stringify({tvCode: tvCode, idAcc: document.getElementById('idAcc').value})
            });
            var data = await request.json();
            showMessage(data.ok ? 'success' : 'error', data.title || (data.ok ? 'Televisión conectada' : 'No fue posible conectar'), data.message || 'Inténtalo nuevamente.');
            if (data.ok) {
                form.reset();
                button.style.display = 'none';
            }
        } catch (error) {
            showMessage('error', 'Problema de conexión', 'No pudimos completar la solicitud. Revisa tu internet e inténtalo nuevamente.');
        } finally {
            button.disabled = false;
            button.classList.remove('loading');
            button.querySelector('span').textContent = 'Vincular mi televisión';
        }
    });

    function showMessage(type, title, message) {
        responseBox.className = 'response ' + type + ' visible';
        responseBox.innerHTML = '';
        var strong = document.createElement('strong');
        var span = document.createElement('span');
        strong.textContent = title;
        span.textContent = message;
        responseBox.appendChild(strong);
        responseBox.appendChild(span);
    }
})();
</script>
<?php endif; ?>
</body>
</html>
