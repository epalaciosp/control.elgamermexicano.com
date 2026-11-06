<?php
// Additional Universal+ alias. No credentials, network, mailbox or log writes.
function universal_activation_normalize_subject($subject) {
    if (!is_string($subject) || !mb_check_encoding($subject, 'UTF-8')) {
        return '';
    }
    if (class_exists('Normalizer')) {
        $subject = Normalizer::normalize($subject, Normalizer::FORM_C);
    }
    return mb_strtolower(trim(preg_replace('/[\s\p{Z}]+/u', ' ', $subject)), 'UTF-8');
}

function universal_activation_matches($message) {
    return is_array($message)
        && isset($message['sender_email'], $message['subject'])
        && is_string($message['sender_email'])
        && strcasecmp(trim($message['sender_email']), 'no-reply@universalplus.com') === 0
        && universal_activation_normalize_subject($message['subject']) === 'universal+ código de activación';
}

function universal_activation_code($message) {
    if (!universal_activation_matches($message) || !is_string($message['content'] ?? null)) {
        return null;
    }
    // Ignore CSS, script and attributes; only visible text may contain a code.
    $body = preg_replace('~<(script|style)\b[^>]*>.*?</\1>~is', '', $message['content']);
    $body = strip_tags(preg_replace('~<[^>]*>~s', ' ', $body));
    $body = html_entity_decode($body, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    preg_match_all('/(?<![A-Za-z0-9])[A-Z0-9]{6}(?![A-Za-z0-9])/u', $body, $matches);
    $codes = array_values(array_unique($matches[0]));
    // Do not guess when more than one distinct token is present.
    return count($codes) === 1 ? $codes[0] : null;
}

function universal_activation_render($code) {
    if (!is_string($code) || !preg_match('/^[A-Z0-9]{6}$/D', $code)) {
        return '<section data-service="UNIVERSAL" role="status"><p>No se encontró un código de activación válido en este mensaje.</p></section>';
    }
    return '<section data-service="UNIVERSAL" role="status" aria-label="Código de activación Universal+">'
        . '<h2>Tu código de activación Universal+</h2>'
        . '<p><strong data-universal-code style="font-size:2rem;letter-spacing:.15em;overflow-wrap:anywhere">'
        . htmlspecialchars($code, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')
        . '</strong></p><p>Usa este código en Universal+.</p></section>';
}
