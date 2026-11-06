"""Exact, credential-preserving portal patch; never exports original PHP files."""
import hashlib

BASELINES = {
    'inbox.php': 'df42df28fbb37b4d09ed96967e19a2dc3642121a762246ac2ccfa9ecbd832916',
    'message.php': 'd19ed5d0ef0b0fd75ce214832ee4913c51addba71a05c4edf7a02c0937fa315d',
}

def once(source, before, after):
    assert source.count(before) == 1, 'PATCH_ANCHOR_MISMATCH'
    return source.replace(before, after, 1)

def transform(name, source, verify=True):
    if verify:
        assert hashlib.sha256(source).hexdigest() == BASELINES[name], 'PRODUCTION_BASELINE_CHANGED'
    source = once(source, b'session_start();', b"session_start();\nrequire_once __DIR__ . '/universal_activation.php';")
    if name == 'inbox.php':
        source = once(source,
            b'function($message) use ($allowed_subjects) {',
            b'function($message) use ($allowed_subjects) {\n    if (universal_activation_matches($message)) { return true; }')
        source = once(source,
            b'$latest_messages = array_slice($filtered_messages, 0, 5);',
            b'''$latest_messages = array_slice($filtered_messages, 0, 5);
// API returns newest messages first; select the first valid Universal+ code.
$universal_activation_result = null;
foreach ($filtered_messages as $candidate) {
    $candidate_code = universal_activation_code($candidate);
    if ($candidate_code !== null) {
        $universal_activation_result = $candidate_code;
        break;
    }
}''')
        source = once(source, b'                <ul>', b'''                <?php if ($universal_activation_result !== null): ?>
                    <?php echo universal_activation_render($universal_activation_result); ?>
                <?php endif; ?>
                <ul>''')
    else:
        source = once(source, b'$subject_allowed = false;', b'$subject_allowed = universal_activation_matches($message);')
        original = b"$content = !empty($message['content']) ? $message['content'] : 'Sin contenido';"
        source = once(source, original,
            b'''if (universal_activation_matches($message)) {
    $content = universal_activation_render(universal_activation_code($message));
} else {
    ''' + original + b'\n}')
    return source
