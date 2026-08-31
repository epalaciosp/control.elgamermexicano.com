<?php
declare(strict_types=1);
require_once __DIR__ . '/admin_bootstrap.php';
$flash = egm_take_flash();
?>
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#080b10">
    <title>Nueva cuenta Netflix | EL GAMER MX</title>
    <link rel="icon" type="image/png" href="/images/favicon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/styles/activation-admin.css?v=20260829a1">
</head>
<body>
<header class="topbar"><a href="cuentas.php" class="brand"><img src="/images/logo-horizontal.png" alt="EL GAMER MX"></a><nav><a class="nav-link secondary" href="cuentas.php">← Regresar al listado</a><span class="user-badge"><?= egm_h(egm_owner()) ?></span></nav></header>
<main class="shell narrow">
    <section class="editor-card">
        <span class="eyebrow">NETFLIX TV VIP</span><h1>Agregar una cuenta</h1>
        <p>Guarda las credenciales y la cookie de sesión. El sistema generará automáticamente cinco enlaces independientes para televisión.</p>
        <?php if ($flash): ?><div class="flash <?= egm_h($flash['type']) ?>"><?= egm_h($flash['message']) ?></div><?php endif; ?>
        <form action="save.php" method="post" class="editor-form">
            <input type="hidden" name="csrf" value="<?= egm_h(egm_csrf()) ?>">
            <label><span>Correo de Netflix</span><input type="email" name="email" placeholder="cuenta@correo.com" required autocomplete="off"></label>
            <label><span>Contraseña</span><input type="password" name="password" placeholder="Contraseña de la cuenta" required autocomplete="new-password"></label>
            <label><span>Cookie de sesión</span><textarea name="cookies" rows="8" placeholder="Pega la cookie como texto o JSON" required></textarea></label>
            <div class="security-note"><strong>Antes de guardar</strong><span>Comprueba que Netflix abre correctamente en el navegador donde obtuviste la cookie. Después podrás validarla desde el listado.</span></div>
            <div class="form-actions"><button type="submit" class="primary-button">Guardar y generar enlaces</button><a href="cuentas.php" class="action-button">Cancelar</a></div>
        </form>
    </section>
</main>
</body>
</html>
