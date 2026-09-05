<?php
declare(strict_types=1);

if (session_status() !== PHP_SESSION_ACTIVE) {
    session_set_cookie_params([
        'httponly' => true,
        'secure' => !empty($_SERVER['HTTPS']),
        'samesite' => 'Strict',
    ]);
    session_start();
}

require_once __DIR__ . '/config.php';

function egm_h(?string $value): string
{
    return htmlspecialchars((string) $value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function egm_owner(): string
{
    $authenticatedOwner = (string) (
        $_SERVER['PHP_AUTH_USER']
        ?? $_SERVER['REMOTE_USER']
        ?? $_SERVER['REDIRECT_REMOTE_USER']
        ?? ''
    );

    if ($authenticatedOwner !== '') {
        $_SESSION['egm_owner'] = $authenticatedOwner;
        return $authenticatedOwner;
    }

    return (string) ($_SESSION['egm_owner'] ?? '');
}

function egm_csrf(): string
{
    if (empty($_SESSION['egm_csrf'])) {
        $_SESSION['egm_csrf'] = bin2hex(random_bytes(24));
    }
    return $_SESSION['egm_csrf'];
}

function egm_verify_csrf(): void
{
    $provided = (string) ($_POST['csrf'] ?? '');
    if ($provided === '' || !hash_equals(egm_csrf(), $provided)) {
        http_response_code(419);
        exit('La sesión expiró. Regresa al listado y vuelve a intentarlo.');
    }
}

function egm_flash(string $type, string $message): void
{
    $_SESSION['egm_flash'] = ['type' => $type, 'message' => $message];
}

function egm_take_flash(): ?array
{
    $flash = $_SESSION['egm_flash'] ?? null;
    unset($_SESSION['egm_flash']);
    return is_array($flash) ? $flash : null;
}

function egm_redirect(string $location = 'cuentas.php'): void
{
    header('Location: ' . $location, true, 303);
    exit;
}

function egm_decode_slot(?string $json): array
{
    $slot = json_decode((string) $json, true);
    return is_array($slot) ? $slot : [];
}

function egm_slot_is_used(array $slot): bool
{
    return ($slot['use'] ?? 'false') === 'true';
}

function egm_new_code(): string
{
    $alphabet = 'abcdefghijkmnopqrstuvwxyz23456789';
    $parts = [];
    for ($part = 0; $part < 4; $part++) {
        $value = '';
        for ($i = 0; $i < 7; $i++) {
            $value .= $alphabet[random_int(0, strlen($alphabet) - 1)];
        }
        $parts[] = $value;
    }
    return implode('-', $parts);
}

function egm_owner_account(mysqli $conn, int $id, string $owner): ?array
{
    $stmt = $conn->prepare('SELECT * FROM cuentas WHERE id = ? AND ownerAccount = ? LIMIT 1');
    $stmt->bind_param('is', $id, $owner);
    $stmt->execute();
    $row = $stmt->get_result()->fetch_assoc() ?: null;
    $stmt->close();
    return $row;
}
