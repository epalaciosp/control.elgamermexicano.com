<?php
declare(strict_types=1);
require_once __DIR__ . '/admin_bootstrap.php';

$owner = egm_owner();
$id = filter_input(INPUT_GET, 'id', FILTER_VALIDATE_INT) ?: filter_input(INPUT_POST, 'id', FILTER_VALIDATE_INT) ?: 0;
$account = $id ? egm_owner_account($conn, $id, $owner) : null;
if (!$account) {
    http_response_code(404);
    exit('Cuenta no encontrada.');
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    egm_verify_csrf();
    $email = trim((string) ($_POST['email'] ?? ''));
    $password = (string) ($_POST['password'] ?? '');
    $cookies = trim((string) ($_POST['cookies'] ?? ''));
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $error = 'Ingresa un correo válido.';
    } else {
        if ($password !== '' && $cookies !== '') {
            $stmt = $conn->prepare("UPDATE cuentas SET email = ?, password = ?, cookies = ?, cookie_status = 'unknown', cookie_checked_at = NULL, cookie_message = NULL WHERE id = ? AND ownerAccount = ?");
            $stmt->bind_param('sssis', $email, $password, $cookies, $id, $owner);
        } elseif ($password !== '') {
            $stmt = $conn->prepare('UPDATE cuentas SET email = ?, password = ? WHERE id = ? AND ownerAccount = ?');
            $stmt->bind_param('ssis', $email, $password, $id, $owner);
        } elseif ($cookies !== '') {
            $stmt = $conn->prepare("UPDATE cuentas SET email = ?, cookies = ?, cookie_status = 'unknown', cookie_checked_at = NULL, cookie_message = NULL WHERE id = ? AND ownerAccount = ?");
            $stmt->bind_param('ssis', $email, $cookies, $id, $owner);
        } else {
            $stmt = $conn->prepare('UPDATE cuentas SET email = ? WHERE id = ? AND ownerAccount = ?');
            $stmt->bind_param('sis', $email, $id, $owner);
        }
        $stmt->execute();
        $stmt->close();
        egm_flash('success', 'Cuenta actualizada. La contraseña y la cookie nunca se muestran en el listado.');
        egm_redirect();
    }
}
?>
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#080b10">
    <title>Editar cuenta | EL GAMER MX</title>
    <link rel="icon" type="image/png" href="/images/favicon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/styles/activation-admin.css?v=20260829a1">
</head>
<body>
<header class="topbar"><a href="cuentas.php" class="brand"><img src="/images/logo-horizontal.png" alt="EL GAMER MX"></a><nav><a class="nav-link secondary" href="cuentas.php">← Regresar</a></nav></header>
<main class="shell narrow">
    <section class="editor-card">
        <span class="eyebrow">CUENTA NETFLIX</span><h1>Actualizar credenciales y cookie</h1>
        <p>Por seguridad los valores actuales no se muestran. Deja en blanco la contraseña o la cookie si no quieres cambiarlas.</p>
        <?php if (!empty($error)): ?><div class="flash error"><?= egm_h($error) ?></div><?php endif; ?>
        <form method="post" class="editor-form">
            <input type="hidden" name="csrf" value="<?= egm_h(egm_csrf()) ?>"><input type="hidden" name="id" value="<?= $id ?>">
            <label><span>Correo de Netflix</span><input type="email" name="email" value="<?= egm_h($account['email']) ?>" required autocomplete="off"></label>
            <label><span>Nueva contraseña <small>opcional</small></span><input type="password" name="password" placeholder="Dejar vacío para conservarla" autocomplete="new-password"></label>
            <label><span>Nueva cookie <small>opcional</small></span><textarea name="cookies" rows="7" placeholder="Pega aquí la cookie nueva; se puede recibir como texto o JSON"></textarea></label>
            <div class="security-note"><strong>Protección de datos</strong><span>La contraseña y la cookie no se vuelven a mostrar después de guardar.</span></div>
            <div class="form-actions"><button type="submit" class="primary-button">Guardar cambios</button><a href="cuentas.php" class="action-button">Cancelar</a></div>
        </form>
    </section>
</main>
</body>
</html>
