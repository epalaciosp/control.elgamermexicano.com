"""Client for the Multiplataforma Partner media APIs.

Credentials live only in the server environment. The provider authorizes the
KVM4 public IPv4, so this module deliberately uses IPv4 even when the host also
has a preferred IPv6 route.
"""

import http.client
import json
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPSHandler, Request, build_opener

from django.core.cache import cache


BASE_URL = os.environ.get(
    "MULTIPLATAFORMA_PARTNER_API_URL",
    "https://multiplataforma.co/api/partner/v1/",
).rstrip("/") + "/"
USERNAME = os.environ.get("MULTIPLATAFORMA_PARTNER_USERNAME", "").strip()
PASSWORD = os.environ.get("MULTIPLATAFORMA_PARTNER_PASSWORD", "")
SERVICE_LABELS = {
    "plex": "Plex",
    "emby": "Emby",
    "jellyfin": "Jellyfin",
}


def _create_ipv4_connection(
    address,
    timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
    source_address=None,
):
    host, port = address
    last_error = None
    for family, socktype, proto, _, sockaddr in socket.getaddrinfo(
        host,
        port,
        socket.AF_INET,
        socket.SOCK_STREAM,
    ):
        sock = None
        try:
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            last_error = exc
            if sock is not None:
                sock.close()
    if last_error is not None:
        raise last_error
    raise OSError("No se encontró una ruta IPv4 para la API Partner")


class _IPv4HTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        self.sock = _create_ipv4_connection(
            (self.host, self.port),
            self.timeout,
            self.source_address,
        )
        server_hostname = self.host
        if self._tunnel_host:
            server_hostname = self._tunnel_host
            self._tunnel()
        self.sock = self._context.wrap_socket(
            self.sock,
            server_hostname=server_hostname,
        )


class _IPv4HTTPSHandler(HTTPSHandler):
    def https_open(self, request):
        return self.do_open(
            _IPv4HTTPSConnection,
            request,
            context=getattr(self, "_context", None),
        )


_OPENER = build_opener(_IPv4HTTPSHandler())


def partner_api_configured():
    return bool(USERNAME and PASSWORD)


def plex_api_configured():
    """Backward-compatible name used by older templates and views."""
    return partner_api_configured()


def _request_json(path, method="GET", payload=None, token=""):
    body = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "MyPlataforma-Partner/2.0",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(
        BASE_URL + path.lstrip("/"),
        data=body,
        headers=headers,
        method=method,
    )
    with _OPENER.open(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _access_token(force_refresh=False):
    cache_key = "multiplataforma_partner_access_token"
    if force_refresh:
        cache.delete(cache_key)
    token = cache.get(cache_key)
    if token:
        return token
    payload = _request_json(
        "auth/token/",
        method="POST",
        payload={"username": USERNAME, "password": PASSWORD},
    )
    token = payload.get("data", {}).get("tokens", {}).get("access", "")
    if token:
        cache.set(cache_key, token, 240)
    return token


def _authorized_request(path, method="GET", payload=None):
    token = _access_token()
    if not token:
        raise ValueError("La API no devolvió un token válido")
    try:
        return _request_json(path, method=method, payload=payload, token=token)
    except HTTPError as exc:
        if exc.code != 401:
            raise
    token = _access_token(force_refresh=True)
    if not token:
        raise ValueError("La API no devolvió un token válido")
    return _request_json(path, method=method, payload=payload, token=token)


def _error_message(exc):
    if isinstance(exc, HTTPError):
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            detail = payload.get("error", {}).get("message")
        except (ValueError, UnicodeDecodeError):
            detail = None
        if exc.code == 403:
            return detail or "La IP fija del KVM4 no está autorizada."
        return detail or "La API Partner respondió con error {}.".format(exc.code)
    if isinstance(exc, ValueError):
        return str(exc)
    return "No fue posible consultar la API Partner en este momento."


def _absolute_asset_url(value):
    if not value:
        return ""
    base = urlsplit(BASE_URL)
    origin = "{}://{}".format(base.scheme, base.netloc)
    return urljoin(origin + "/", str(value).lstrip("/"))


def get_media_market(service):
    """Return the live Plex, Emby or Jellyfin market and provider balance."""
    service = str(service).strip().lower()
    if service not in SERVICE_LABELS:
        return {}, "Servicio multimedia no válido."
    if not partner_api_configured():
        return {}, "La integración API Partner todavía no está configurada."

    variants = (None,) if service == "plex" else (0, 1)
    market = {
        "service": service,
        "label": SERVICE_LABELS[service],
        "balance": 0,
        "currency_code": "",
        "currency_prefix": "",
        "plans": [],
    }
    try:
        for tv in variants:
            path = service + "/market/"
            if tv is not None:
                path += "?" + urlencode({"tv": tv})
            data = _authorized_request(path).get("data", {})
            market["label"] = data.get("platform_label") or market["label"]
            market["balance"] = data.get("balance", market["balance"])
            market["currency_code"] = data.get(
                "currency_code",
                market["currency_code"],
            )
            market["currency_prefix"] = data.get(
                "currency_prefix",
                market["currency_prefix"],
            )
            for source_plan in data.get("plans", []):
                plan = dict(source_plan)
                if tv is not None:
                    plan["with_tv"] = bool(plan.get("with_tv", tv))
                plan["logo_url"] = _absolute_asset_url(plan.get("logo_url"))
                market["plans"].append(plan)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return {}, _error_message(exc)

    market["plans"].sort(
        key=lambda plan: (
            bool(plan.get("with_tv")),
            float(plan.get("price") or 0),
            int(plan.get("connections") or 0),
            int(plan.get("plan_id") or 0),
        )
    )
    return market, None


def get_plex_market():
    """Compatibility wrapper for the original read-only Plex module."""
    market, error = get_media_market("plex")
    return market.get("plans", []), error


def get_media_accounts(service, page=1, page_size=20, search=""):
    service = str(service).strip().lower()
    if service not in SERVICE_LABELS:
        return {}, "Servicio multimedia no válido."
    query = urlencode({
        "page": max(int(page), 1),
        "page_size": min(max(int(page_size), 1), 100),
        "search": str(search).strip(),
    })
    try:
        payload = _authorized_request(service + "/accounts/?" + query)
        return payload.get("data", {}), None
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return {}, _error_message(exc)


def purchase_media_account(service, plan_id, account, password, customer):
    """Low-level purchase call; UI activation requires a configured sale price."""
    service = str(service).strip().lower()
    if service not in SERVICE_LABELS:
        return {}, "Servicio multimedia no válido."
    try:
        payload = _authorized_request(
            service + "/accounts/",
            method="POST",
            payload={
                "plan_id": int(plan_id),
                "email": str(account).strip(),
                "password": str(password),
                "customer": str(customer).strip(),
            },
        )
        return payload.get("data", {}), None
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return {}, _error_message(exc)
