"""Private client for the Multiplataforma Partner media catalogs.

Only Control uses the provider balance and acquisition prices.  Customer-facing
views receive sale prices stored in Control instead of this raw response.
"""

import http.client
import json
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPSHandler, Request, build_opener

from django.core.cache import cache


BASE_URL = os.environ.get(
    "MULTIPLATAFORMA_PARTNER_API_URL",
    "https://multiplataforma.co/api/partner/v1/",
).rstrip("/") + "/"
USERNAME = os.environ.get("MULTIPLATAFORMA_PARTNER_USERNAME", "").strip()
PASSWORD = os.environ.get("MULTIPLATAFORMA_PARTNER_PASSWORD", "")
SERVICES = ("plex", "emby", "jellyfin")


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


def _request_json(path, method="GET", payload=None, token=""):
    body = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "Control-ElGamerMX/1.0",
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
    with _OPENER.open(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _access_token(force_refresh=False):
    cache_key = "control_partner_media_access_token"
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


def _authorized_request(path):
    token = _access_token()
    if not token:
        raise ValueError("La API no devolvió un token válido")
    try:
        return _request_json(path, token=token)
    except HTTPError as exc:
        if exc.code != 401:
            raise
    token = _access_token(force_refresh=True)
    if not token:
        raise ValueError("La API no devolvió un token válido")
    return _request_json(path, token=token)


def _error_message(exc):
    if isinstance(exc, HTTPError):
        if exc.code == 403:
            return "La IP fija del KVM4 no está autorizada por el proveedor."
        return "La API Partner respondió con error {}.".format(exc.code)
    if isinstance(exc, ValueError):
        return str(exc)
    return "No fue posible consultar la API Partner en este momento."


def get_partner_media_markets():
    """Return normalized provider plans and the private provider balance."""
    if not partner_api_configured():
        return [], {}, "La API Partner todavía no está configurada en Control."

    plans = []
    provider = {"balance": 0, "currency_prefix": "", "currency_code": ""}
    try:
        for service in SERVICES:
            variants = (None,) if service == "plex" else (0, 1)
            for tv in variants:
                path = service + "/market/"
                if tv is not None:
                    path += "?" + urlencode({"tv": tv})
                data = _authorized_request(path).get("data", {})
                provider["balance"] = data.get("balance", provider["balance"])
                provider["currency_prefix"] = data.get(
                    "currency_prefix",
                    provider["currency_prefix"],
                )
                provider["currency_code"] = data.get(
                    "currency_code",
                    provider["currency_code"],
                )
                for source_plan in data.get("plans", []):
                    plan = dict(source_plan)
                    plan["service"] = service
                    plan["with_tv"] = bool(plan.get("with_tv", tv or False))
                    plans.append(plan)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return [], provider, _error_message(exc)
    return plans, provider, None
