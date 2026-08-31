<?php
declare(strict_types=1);
require_once __DIR__ . '/admin_bootstrap.php';

$owner = egm_owner();
if ($owner === '') {
    http_response_code(401);
    exit('Acceso no autorizado.');
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    egm_verify_csrf();
    $action = (string) ($_POST['action'] ?? '');
    $id = filter_input(INPUT_POST, 'id', FILTER_VALIDATE_INT) ?: 0;
    $account = $id ? egm_owner_account($conn, $id, $owner) : null;

    if (!$account) {
        egm_flash('error', 'No se encontró la cuenta solicitada.');
        egm_redirect();
    }

    if ($action === 'archive' || $action === 'restore') {
        $archivedAt = $action === 'archive' ? date('Y-m-d H:i:s') : null;
        $stmt = $conn->prepare('UPDATE cuentas SET archived_at = ? WHERE id = ? AND ownerAccount = ?');
        $stmt->bind_param('sis', $archivedAt, $id, $owner);
        $stmt->execute();
        $stmt->close();
        egm_flash('success', $action === 'archive' ? 'Cuenta archivada. No se eliminó ningún dato.' : 'Cuenta restaurada correctamente.');
        egm_redirect();
    }

    if ($action === 'restart') {
        $slotNumber = filter_input(INPUT_POST, 'slot', FILTER_VALIDATE_INT) ?: 0;
        if ($slotNumber < 1 || $slotNumber > 5) {
            egm_flash('error', 'El espacio seleccionado no es válido.');
            egm_redirect();
        }
        $column = 'code' . $slotNumber;
        $slot = [
            'code' => egm_new_code(),
            'dispositivo' => 'not linked',
            'use' => 'false',
            'date_reg' => '0000-00-00 00:00:00',
        ];
        $json = json_encode($slot, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        $stmt = $conn->prepare("UPDATE cuentas SET {$column} = ? WHERE id = ? AND ownerAccount = ?");
        $stmt->bind_param('sis', $json, $id, $owner);
        $stmt->execute();
        $stmt->close();
        egm_flash('success', 'Se generó un enlace nuevo para el espacio ' . $slotNumber . '.');
        egm_redirect();
    }

    if ($action === 'check_cookie') {
        require_once __DIR__ . '/f.php';
        $check = netflixSessionStatus((string) $account['cookies']);
        $status = in_array($check['status'], ['valid', 'expired', 'error'], true) ? $check['status'] : 'error';
        $message = mb_substr((string) $check['message'], 0, 250);
        $checkedAt = date('Y-m-d H:i:s');
        $stmt = $conn->prepare('UPDATE cuentas SET cookie_status = ?, cookie_checked_at = ?, cookie_message = ? WHERE id = ? AND ownerAccount = ?');
        $stmt->bind_param('sssis', $status, $checkedAt, $message, $id, $owner);
        $stmt->execute();
        $stmt->close();
        egm_flash($status === 'valid' ? 'success' : 'warning', $message);
        egm_redirect();
    }
}

$stmt = $conn->prepare('SELECT * FROM cuentas WHERE ownerAccount = ? ORDER BY archived_at IS NOT NULL, reg_date DESC, id DESC');
$stmt->bind_param('s', $owner);
$stmt->execute();
$result = $stmt->get_result();
$allAccounts = [];
$metrics = ['total' => 0, 'active' => 0, 'archived' => 0, 'valid' => 0, 'expired' => 0, 'unknown' => 0, 'used_slots' => 0, 'capacity' => 0, 'unused' => 0];

while ($row = $result->fetch_assoc()) {
    $row['slots'] = [];
    $row['used_slots'] = 0;
    for ($i = 1; $i <= 5; $i++) {
        $slot = egm_decode_slot($row['code' . $i] ?? '');
        $row['slots'][$i] = $slot;
        if (egm_slot_is_used($slot)) {
            $row['used_slots']++;
        }
    }
    $metrics['total']++;
    if ($row['archived_at']) {
        $metrics['archived']++;
    } else {
        $metrics['active']++;
        $metrics['capacity'] += 5;
        $metrics['used_slots'] += $row['used_slots'];
    }
    if ($row['used_slots'] === 0) {
        $metrics['unused']++;
    }
    $cookieMetric = in_array($row['cookie_status'], ['valid', 'expired'], true) ? $row['cookie_status'] : 'unknown';
    $metrics[$cookieMetric]++;
    $allAccounts[] = $row;
}
$stmt->close();

$search = trim((string) ($_GET['q'] ?? ''));
$view = (string) ($_GET['view'] ?? 'active');
$cookie = (string) ($_GET['cookie'] ?? 'all');
$allowedViews = ['active', 'archived', 'unused', 'all'];
$allowedCookie = ['all', 'valid', 'expired', 'unknown', 'error'];
if (!in_array($view, $allowedViews, true)) $view = 'active';
if (!in_array($cookie, $allowedCookie, true)) $cookie = 'all';

$filtered = array_values(array_filter($allAccounts, static function (array $row) use ($search, $view, $cookie): bool {
    if ($view === 'active' && $row['archived_at']) return false;
    if ($view === 'archived' && !$row['archived_at']) return false;
    if ($view === 'unused' && ($row['archived_at'] || $row['used_slots'] !== 0)) return false;
    if ($cookie !== 'all' && $row['cookie_status'] !== $cookie) return false;
    if ($search !== '' && stripos((string) $row['email'], $search) === false) return false;
    return true;
}));

$perPage = 20;
$totalFiltered = count($filtered);
$pages = max(1, (int) ceil($totalFiltered / $perPage));
$page = min($pages, max(1, (int) ($_GET['page'] ?? 1)));
$accounts = array_slice($filtered, ($page - 1) * $perPage, $perPage);
$flash = egm_take_flash();
$available = max(0, $metrics['capacity'] - $metrics['used_slots']);

function egm_query_url(array $changes = []): string
{
    $query = array_merge($_GET, $changes);
    foreach ($query as $key => $value) if ($value === '' || $value === null) unset($query[$key]);
    return 'cuentas.php?' . http_build_query($query);
}
?>
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#080b10">
    <title>Cuentas Netflix TV | EL GAMER MX</title>
    <link rel="icon" type="image/png" href="/images/favicon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/styles/activation-admin.css?v=20260829a1">
</head>
<body>
<header class="topbar">
    <a href="cuentas.php" class="brand"><img src="/images/logo-horizontal.png" alt="EL GAMER MX"></a>
    <nav>
        <a class="nav-link" href="agregar.php">+ Nueva cuenta</a>
        <?php if (file_exists(__DIR__ . '/cuentascsv.php')): ?><a class="nav-link secondary" href="cuentascsv.php">Importar CSV</a><?php endif; ?>
        <span class="user-badge"><?= egm_h($owner) ?></span>
    </nav>
</header>

<main class="shell">
    <section class="hero">
        <div>
            <span class="eyebrow">NETFLIX TV VIP</span>
            <h1>Administración de cuentas</h1>
            <p>Controla las cookies y enlaces de activación sin mostrar contraseñas ni eliminar información definitivamente.</p>
        </div>
        <a class="primary-button" href="agregar.php">Agregar cuenta</a>
    </section>

    <?php if ($flash): ?>
        <div class="flash <?= egm_h($flash['type']) ?>" role="status"><?= egm_h($flash['message']) ?></div>
    <?php endif; ?>

    <section class="metrics" aria-label="Resumen de cuentas">
        <article><span>Cuentas disponibles</span><strong><?= $metrics['active'] ?></strong><small><?= $metrics['total'] ?> registradas</small></article>
        <article><span>Espacios libres</span><strong><?= $available ?></strong><small><?= $metrics['used_slots'] ?> de <?= $metrics['capacity'] ?> ocupados</small></article>
        <article><span>Sin uso</span><strong><?= $metrics['unused'] ?></strong><small>Sin televisores activos</small></article>
        <article><span>Cookies vencidas</span><strong><?= $metrics['expired'] ?></strong><small><?= $metrics['unknown'] ?> pendientes de validar</small></article>
    </section>

    <section class="toolbar-card">
        <form method="get" class="filters">
            <label class="search-field"><span>Buscar cuenta</span><input type="search" name="q" value="<?= egm_h($search) ?>" placeholder="correo@dominio.com"></label>
            <label><span>Mostrar</span><select name="view">
                <option value="active" <?= $view === 'active' ? 'selected' : '' ?>>Disponibles</option>
                <option value="unused" <?= $view === 'unused' ? 'selected' : '' ?>>Sin uso</option>
                <option value="archived" <?= $view === 'archived' ? 'selected' : '' ?>>Archivadas</option>
                <option value="all" <?= $view === 'all' ? 'selected' : '' ?>>Todas</option>
            </select></label>
            <label><span>Estado de cookie</span><select name="cookie">
                <option value="all" <?= $cookie === 'all' ? 'selected' : '' ?>>Todos</option>
                <option value="valid" <?= $cookie === 'valid' ? 'selected' : '' ?>>Vigente</option>
                <option value="expired" <?= $cookie === 'expired' ? 'selected' : '' ?>>Vencida</option>
                <option value="unknown" <?= $cookie === 'unknown' ? 'selected' : '' ?>>Sin validar</option>
                <option value="error" <?= $cookie === 'error' ? 'selected' : '' ?>>Error de conexión</option>
            </select></label>
            <button type="submit">Aplicar filtros</button>
            <a href="cuentas.php" class="clear-link">Limpiar</a>
        </form>
        <p class="results-count"><?= $totalFiltered ?> cuenta<?= $totalFiltered === 1 ? '' : 's' ?> encontrada<?= $totalFiltered === 1 ? '' : 's' ?></p>
    </section>

    <section class="account-list">
        <?php if (!$accounts): ?>
            <div class="empty-state"><strong>No hay cuentas con estos filtros</strong><span>Prueba otra búsqueda o cambia el estado.</span></div>
        <?php endif; ?>

        <?php foreach ($accounts as $account):
            $status = $account['cookie_status'] ?: 'unknown';
            $statusLabel = ['valid' => 'Cookie vigente', 'expired' => 'Cookie vencida', 'error' => 'Error al validar', 'unknown' => 'Sin validar'][$status] ?? 'Sin validar';
        ?>
            <article class="account-card <?= $account['archived_at'] ? 'is-archived' : '' ?>">
                <div class="account-main">
                    <div class="account-identity">
                        <span class="netflix-mark">N</span>
                        <div><h2><?= egm_h($account['email']) ?></h2><p>Registrada <?= egm_h(date('d/m/Y', strtotime($account['reg_date']))) ?> · ID <?= (int) $account['id'] ?></p></div>
                    </div>
                    <div class="account-summary">
                        <span class="health <?= egm_h($status) ?>"><i></i><?= egm_h($statusLabel) ?></span>
                        <span class="usage"><b><?= (int) $account['used_slots'] ?>/5</b> televisores</span>
                    </div>
                    <div class="account-actions">
                        <?php if (!$account['archived_at']): ?>
                            <form method="post"><input type="hidden" name="csrf" value="<?= egm_h(egm_csrf()) ?>"><input type="hidden" name="action" value="check_cookie"><input type="hidden" name="id" value="<?= (int) $account['id'] ?>"><button class="action-button check" type="submit">Validar cookie</button></form>
                            <a class="action-button" href="editar_cuenta.php?id=<?= (int) $account['id'] ?>">Editar</a>
                        <?php endif; ?>
                        <form method="post" onsubmit="return confirm('<?= $account['archived_at'] ? '¿Restaurar esta cuenta?' : '¿Archivar esta cuenta? No se borrará ningún dato.' ?>')"><input type="hidden" name="csrf" value="<?= egm_h(egm_csrf()) ?>"><input type="hidden" name="action" value="<?= $account['archived_at'] ? 'restore' : 'archive' ?>"><input type="hidden" name="id" value="<?= (int) $account['id'] ?>"><button class="action-button <?= $account['archived_at'] ? 'restore' : 'archive' ?>" type="submit"><?= $account['archived_at'] ? 'Restaurar' : 'Archivar' ?></button></form>
                    </div>
                </div>

                <?php if ($account['cookie_message']): ?><p class="cookie-message"><?= egm_h($account['cookie_message']) ?><?php if ($account['cookie_checked_at']): ?> · <?= egm_h(date('d/m/Y H:i', strtotime($account['cookie_checked_at']))) ?><?php endif; ?></p><?php endif; ?>

                <details class="slots-panel">
                    <summary>Ver enlaces y espacios <span>▾</span></summary>
                    <div class="slots-grid">
                        <?php foreach ($account['slots'] as $slotNumber => $slot):
                            $isUsed = egm_slot_is_used($slot);
                            $code = (string) ($slot['code'] ?? '');
                            $activationUrl = 'https://activacion.elgamermexicano.com/?id=' . rawurlencode($code);
                        ?>
                            <div class="slot <?= $isUsed ? 'used' : 'free' ?>">
                                <div class="slot-title"><strong>Espacio <?= $slotNumber ?></strong><span><?= $isUsed ? 'En uso' : 'Disponible' ?></span></div>
                                <p><?= $isUsed ? egm_h((string) ($slot['dispositivo'] ?? 'TV vinculada')) : 'Listo para enviar a un cliente' ?></p>
                                <div class="slot-actions">
                                    <button type="button" class="copy-link" data-copy="<?= egm_h($activationUrl) ?>">Copiar enlace</button>
                                    <form method="post" onsubmit="return confirm('¿Generar un enlace nuevo para este espacio? El enlace anterior dejará de aparecer en el panel.')"><input type="hidden" name="csrf" value="<?= egm_h(egm_csrf()) ?>"><input type="hidden" name="action" value="restart"><input type="hidden" name="id" value="<?= (int) $account['id'] ?>"><input type="hidden" name="slot" value="<?= $slotNumber ?>"><button type="submit">Reiniciar</button></form>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    </div>
                </details>
            </article>
        <?php endforeach; ?>
    </section>

    <?php if ($pages > 1): ?>
        <nav class="pagination" aria-label="Paginación">
            <?php if ($page > 1): ?><a href="<?= egm_h(egm_query_url(['page' => $page - 1])) ?>">Anterior</a><?php endif; ?>
            <span>Página <?= $page ?> de <?= $pages ?></span>
            <?php if ($page < $pages): ?><a href="<?= egm_h(egm_query_url(['page' => $page + 1])) ?>">Siguiente</a><?php endif; ?>
        </nav>
    <?php endif; ?>
</main>

<script>
document.querySelectorAll('[data-copy]').forEach(function (button) {
    button.addEventListener('click', function () {
        navigator.clipboard.writeText(button.dataset.copy).then(function () {
            var previous = button.textContent;
            button.textContent = 'Enlace copiado';
            setTimeout(function () { button.textContent = previous; }, 1600);
        });
    });
});
</script>
</body>
</html>
