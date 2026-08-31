<?php
declare(strict_types=1);

function netflixNormalizeCookies(string $cookies): string
{
    $cookies = trim($cookies);
    if ($cookies === '') {
        return '';
    }

    $decoded = json_decode($cookies, true);
    if (!is_array($decoded)) {
        return preg_replace('/[\r\n]+/', '; ', $cookies) ?? $cookies;
    }

    $pairs = [];
    foreach ($decoded as $key => $item) {
        if (is_array($item) && isset($item['name'], $item['value'])) {
            $pairs[] = $item['name'] . '=' . $item['value'];
        } elseif (is_string($key) && is_scalar($item)) {
            $pairs[] = $key . '=' . (string) $item;
        }
    }
    return $pairs ? implode('; ', $pairs) : $cookies;
}

function netflixRequest(string $url, string $cookies, ?array $post = null): array
{
    $curl = curl_init($url);
    $headers = [
        'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'accept-language: es-MX,es;q=0.9,en;q=0.7',
        'cache-control: no-cache',
        'origin: https://www.netflix.com',
        'referer: https://www.netflix.com/tv2',
    ];

    curl_setopt_array($curl, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HEADER => true,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_CONNECTTIMEOUT => 12,
        CURLOPT_TIMEOUT => 25,
        CURLOPT_SSL_VERIFYHOST => 2,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_ENCODING => '',
        CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_COOKIE => netflixNormalizeCookies($cookies),
    ]);

    if ($post !== null) {
        curl_setopt($curl, CURLOPT_POST, true);
        curl_setopt($curl, CURLOPT_POSTFIELDS, http_build_query($post, '', '&', PHP_QUERY_RFC3986));
        curl_setopt($curl, CURLOPT_HTTPHEADER, array_merge($headers, [
            'content-type: application/x-www-form-urlencoded',
        ]));
    }

    $raw = curl_exec($curl);
    $error = curl_error($curl);
    $status = (int) curl_getinfo($curl, CURLINFO_HTTP_CODE);
    $headerSize = (int) curl_getinfo($curl, CURLINFO_HEADER_SIZE);
    $redirect = (string) curl_getinfo($curl, CURLINFO_REDIRECT_URL);
    curl_close($curl);

    if ($raw === false) {
        return ['ok' => false, 'status' => $status, 'error' => $error ?: 'No se recibió respuesta', 'headers' => '', 'body' => '', 'redirect' => ''];
    }

    return [
        'ok' => true,
        'status' => $status,
        'error' => '',
        'headers' => substr($raw, 0, $headerSize),
        'body' => substr($raw, $headerSize),
        'redirect' => $redirect,
    ];
}

function netflixAuthUrl(string $cookies): array
{
    if (netflixNormalizeCookies($cookies) === '') {
        return ['ok' => false, 'status' => 'expired', 'message' => 'La cuenta no tiene una cookie guardada.', 'auth' => ''];
    }

    $response = netflixRequest('https://www.netflix.com/tv2', $cookies);
    if (!$response['ok']) {
        return ['ok' => false, 'status' => 'error', 'message' => 'No fue posible comunicarse con Netflix.', 'auth' => ''];
    }

    $body = (string) $response['body'];
    $auth = '';
    if (preg_match('/name=["\']authURL["\'][^>]*value=["\']([^"\']+)["\']/i', $body, $match)
        || preg_match('/value=["\']([^"\']+)["\'][^>]*name=["\']authURL["\']/i', $body, $match)) {
        $auth = html_entity_decode($match[1], ENT_QUOTES | ENT_HTML5, 'UTF-8');
    }

    if ($auth === '') {
        return ['ok' => false, 'status' => 'expired', 'message' => 'Netflix rechazó la sesión. Es necesario renovar la cookie.', 'auth' => ''];
    }

    return ['ok' => true, 'status' => 'valid', 'message' => 'Cookie vigente y lista para vincular una TV.', 'auth' => $auth];
}

function netflixSessionStatus(string $cookies): array
{
    $result = netflixAuthUrl($cookies);
    unset($result['auth']);
    return $result;
}

function returnAuth($cookies)
{
    $result = netflixAuthUrl((string) $cookies);
    return $result['ok'] ? $result['auth'] : '';
}

function authorize($code, $cookies)
{
    $auth = netflixAuthUrl((string) $cookies);
    if (!$auth['ok']) {
        return false;
    }

    $code = trim((string) $code);
    $response = netflixRequest('https://www.netflix.com/tv2', (string) $cookies, [
        'flow' => 'websiteSignUp',
        'authURL' => $auth['auth'],
        'flowMode' => 'enterTvLoginRendezvousCode',
        'withFields' => 'tvLoginRendezvousCode,isTvUrl2',
        'code' => $code,
        'tvLoginRendezvousCode' => $code,
        'isTvUrl2' => 'true',
        'action' => 'nextAction',
    ]);

    if (!$response['ok']) {
        return false;
    }

    $location = $response['redirect'];
    if ($location === '' && preg_match('/^location:\s*(.+)$/mi', (string) $response['headers'], $match)) {
        $location = trim($match[1]);
    }

    $path = (string) parse_url($location, PHP_URL_PATH);
    if (rtrim($path, '/') === '/tv/out/success') {
        return true;
    }

    return stripos((string) $response['body'], '/tv/out/success') !== false;
}
