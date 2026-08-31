<?php
declare(strict_types=1);

ini_set('display_errors', '0');
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/f.php';

function respond(int $status, bool $ok, string $title, string $message): void
{
    http_response_code($status);
    echo json_encode(['ok' => $ok, 'title' => $title, 'message' => $message], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(405, false, 'Solicitud no permitida', 'Abre el enlace de activación y utiliza el formulario.');
}

$payload = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($payload)) {
    respond(400, false, 'Datos incompletos', 'No se recibió correctamente el código de la TV.');
}

$tvCode = preg_replace('/\D/', '', (string) ($payload['tvCode'] ?? ''));
$activationId = preg_replace('/[^a-z0-9-]/i', '', (string) ($payload['idAcc'] ?? ''));
if (!preg_match('/^\d{8}$/', $tvCode)) {
    respond(422, false, 'Código incompleto', 'Escribe los 8 números que aparecen en tu televisión.');
}
if ($activationId === '' || strlen($activationId) < 20) {
    respond(422, false, 'Enlace no válido', 'Solicita un enlace nuevo a atención a clientes.');
}

$search = '%' . $activationId . '%';
$stmt = $conn->prepare('SELECT id, cookies, code1, code2, code3, code4, code5 FROM cuentas WHERE archived_at IS NULL AND (code1 LIKE ? OR code2 LIKE ? OR code3 LIKE ? OR code4 LIKE ? OR code5 LIKE ?) LIMIT 10');
$stmt->bind_param('sssss', $search, $search, $search, $search, $search);
$stmt->execute();
$result = $stmt->get_result();
$account = null;
$slotNumber = 0;
$slot = null;

while ($row = $result->fetch_assoc()) {
    for ($i = 1; $i <= 5; $i++) {
        $candidate = json_decode((string) $row['code' . $i], true);
        if (is_array($candidate) && hash_equals((string) ($candidate['code'] ?? ''), $activationId)) {
            $account = $row;
            $slotNumber = $i;
            $slot = $candidate;
            break 2;
        }
    }
}
$stmt->close();

if (!$account || !$slot || $slotNumber < 1) {
    respond(404, false, 'Enlace no encontrado', 'El enlace pudo haber sido renovado. Solicita uno nuevo a atención a clientes.');
}

if (($slot['use'] ?? 'false') === 'true') {
    $date = !empty($slot['date_reg']) && strtotime((string) $slot['date_reg']) ? date('d/m/Y', strtotime((string) $slot['date_reg'])) : '';
    respond(409, false, 'Enlace utilizado', $date ? 'Este enlace fue utilizado el ' . $date . '. Solicita uno nuevo si cambiaste de TV.' : 'Este enlace ya fue utilizado. Solicita uno nuevo si cambiaste de TV.');
}

$session = netflixSessionStatus((string) $account['cookies']);
if (!$session['ok']) {
    $status = in_array($session['status'], ['expired', 'error'], true) ? $session['status'] : 'error';
    $message = mb_substr((string) $session['message'], 0, 250);
    $checkedAt = date('Y-m-d H:i:s');
    $update = $conn->prepare('UPDATE cuentas SET cookie_status = ?, cookie_checked_at = ?, cookie_message = ? WHERE id = ?');
    $update->bind_param('sssi', $status, $checkedAt, $message, $account['id']);
    $update->execute();
    $update->close();
    respond($status === 'expired' ? 409 : 502, false, $status === 'expired' ? 'Sesión por renovar' : 'Netflix no respondió', $status === 'expired' ? 'La cuenta necesita una cookie nueva. Atención a clientes ya puede identificar el problema.' : 'Hubo un problema temporal al comunicarnos con Netflix. Inténtalo nuevamente.');
}

if (!authorize($tvCode, (string) $account['cookies'])) {
    respond(422, false, 'Código rechazado', 'Verifica que el código siga visible en tu TV y que tenga exactamente 8 números.');
}

$slot['dispositivo'] = 'TV vinculada';
$slot['use'] = 'true';
$slot['date_reg'] = date('Y-m-d H:i:s');
$json = json_encode($slot, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
$column = 'code' . $slotNumber;
$status = 'valid';
$checkedAt = date('Y-m-d H:i:s');
$message = 'Cookie vigente y utilizada correctamente.';
$update = $conn->prepare("UPDATE cuentas SET {$column} = ?, cookie_status = ?, cookie_checked_at = ?, cookie_message = ? WHERE id = ?");
$update->bind_param('ssssi', $json, $status, $checkedAt, $message, $account['id']);
if (!$update->execute()) {
    error_log('No fue posible registrar una activación Netflix para la cuenta ID ' . (int) $account['id']);
    respond(500, false, 'Activación incompleta', 'La TV fue aceptada, pero no pudimos guardar el resultado. Contacta a atención a clientes.');
}
$update->close();

respond(200, true, '¡Televisión conectada!', 'Netflix quedó vinculado correctamente. Ya puedes continuar en tu TV.');
