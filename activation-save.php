<?php
declare(strict_types=1);
require_once __DIR__ . '/admin_bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    egm_redirect('agregar.php');
}
egm_verify_csrf();

$owner = egm_owner();
$email = trim((string) ($_POST['email'] ?? ''));
$password = (string) ($_POST['password'] ?? '');
$cookies = trim((string) ($_POST['cookies'] ?? ''));

if ($owner === '' || !filter_var($email, FILTER_VALIDATE_EMAIL) || $password === '' || $cookies === '') {
    egm_flash('error', 'Completa correctamente el correo, la contraseña y la cookie.');
    egm_redirect('agregar.php');
}

$duplicate = $conn->prepare('SELECT id FROM cuentas WHERE ownerAccount = ? AND email = ? AND archived_at IS NULL LIMIT 1');
$duplicate->bind_param('ss', $owner, $email);
$duplicate->execute();
$exists = (bool) $duplicate->get_result()->fetch_assoc();
$duplicate->close();
if ($exists) {
    egm_flash('warning', 'Ese correo ya está registrado. Edítalo desde el listado para renovar su cookie.');
    egm_redirect('agregar.php');
}

$slots = [];
for ($i = 0; $i < 5; $i++) {
    $slots[] = json_encode([
        'code' => egm_new_code(),
        'dispositivo' => 'not linked',
        'use' => 'false',
        'date_reg' => '0000-00-00 00:00:00',
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
}

$stmt = $conn->prepare("INSERT INTO cuentas (email, password, cookies, code1, code2, code3, code4, code5, ownerAccount, cookie_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unknown')");
$stmt->bind_param('sssssssss', $email, $password, $cookies, $slots[0], $slots[1], $slots[2], $slots[3], $slots[4], $owner);
if (!$stmt->execute()) {
    error_log('No fue posible agregar una cuenta Netflix para el usuario autenticado.');
    $stmt->close();
    egm_flash('error', 'No se pudo guardar la cuenta. Inténtalo nuevamente.');
    egm_redirect('agregar.php');
}
$stmt->close();

egm_flash('success', 'Cuenta guardada y cinco enlaces generados correctamente.');
egm_redirect('cuentas.php');
