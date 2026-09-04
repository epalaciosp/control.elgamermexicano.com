"""Private client for the Multiplataforma Partner media catalogs.

Only Control uses the provider balance and acquisition prices.  Customer-facing
views receive sale prices stored in Control instead of this raw response.
"""

import http.client
import json
import os
import socket
import uuid
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


def _request_multipart_json(
    path,
    fields,
    file_name,
    file_content,
    file_content_type,
    token="",
):
    boundary = "----ControlElGamerMX" + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body.extend(("--" + boundary + "\r\n").encode("ascii"))
        body.extend(
            ('Content-Disposition: form-data; name="{}"\r\n\r\n'.format(name)).encode(
                "utf-8"
            )
        )
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")
    safe_file_name = (
        os.path.basename(str(file_name))
        .replace('"', "")
        .replace("\r", "")
        .replace("\n", "")
    )
    body.extend(("--" + boundary + "\r\n").encode("ascii"))
    body.extend(
        (
            'Content-Disposition: form-data; name="image"; filename="{}"\r\n'.format(
                safe_file_name
            )
        ).encode("utf-8")
    )
    body.extend(("Content-Type: {}\r\n\r\n".format(file_content_type)).encode("ascii"))
    body.extend(file_content)
    body.extend(b"\r\n")
    body.extend(("--" + boundary + "--\r\n").encode("ascii"))
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + token,
        "Content-Type": "multipart/form-data; boundary=" + boundary,
        "User-Agent": "Control-ElGamerMX/1.0",
    }
    request = Request(
        BASE_URL + path.lstrip("/"),
        data=bytes(body),
        headers=headers,
        method="POST",
    )
    with _OPENER.open(request, timeout=45) as response:
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


def _authorized_multipart_request(
    path,
    fields,
    file_name,
    file_content,
    file_content_type,
):
    token = _access_token()
    if not token:
        raise ValueError("La API no devolvió un token válido")
    try:
        return _request_multipart_json(
            path,
            fields,
            file_name,
            file_content,
            file_content_type,
            token=token,
        )
    except HTTPError as exc:
        if exc.code != 401:
            raise
    token = _access_token(force_refresh=True)
    if not token:
        raise ValueError("La API no devolvió un token válido")
    return _request_multipart_json(
        path,
        fields,
        file_name,
        file_content,
        file_content_type,
        token=token,
    )


def _error_message(exc):
    if isinstance(exc, HTTPError):
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            detail = payload.get("error", {})
            if isinstance(detail, dict) and detail.get("message"):
                return str(detail["message"])
            if isinstance(detail, str) and detail:
                return detail
        except (ValueError, UnicodeDecodeError, OSError):
            pass
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


def get_partner_media_market(service):
    """Return one live provider catalog with private balance and costs."""
    service = str(service or "").strip().lower()
    if service not in SERVICES:
        return [], {}, "El servicio solicitado no es válido."
    if not partner_api_configured():
        return [], {}, "La API Partner todavía no está configurada en Control."

    plans = []
    provider = {"balance": 0, "currency_prefix": "", "currency_code": ""}
    try:
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


def purchase_partner_media_account(service, plan_id, email, password, customer):
    """Buy one provider account at the authenticated seller's live cost."""
    service = str(service or "").strip().lower()
    if service not in SERVICES:
        return {}, "El servicio solicitado no es válido."
    if not partner_api_configured():
        return {}, "La API Partner todavía no está configurada en Control."

    normalized_plan_id = str(plan_id).strip()
    if normalized_plan_id.isdigit():
        normalized_plan_id = int(normalized_plan_id)
    payload = {
        "plan_id": normalized_plan_id,
        "email": email,
        "password": password,
        "customer": customer,
    }
    try:
        response = _authorized_request(
            service + "/accounts/",
            method="POST",
            payload=payload,
        )
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return {}, _error_message(exc)

    if not response.get("success", False):
        detail = response.get("error", {})
        if isinstance(detail, dict):
            detail = detail.get("message")
        return {}, str(detail or "El proveedor no pudo generar la cuenta.")
    return response.get("data", {}), None


def get_partner_media_issues(service):
    """Return live issue reports created by this provider account."""
    service = str(service or "").strip().lower()
    if service not in SERVICES:
        return [], {}, "El servicio solicitado no es válido."
    if not partner_api_configured():
        return [], {}, "La API Partner todavía no está configurada en Control."
    try:
        response = _authorized_request(
            "seller/account-issues/?"
            + urlencode({"platform": service, "status": "all", "page_size": 100})
        )
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return [], {}, _error_message(exc)
    if not response.get("success", False):
        detail = response.get("error", {})
        if isinstance(detail, dict):
            detail = detail.get("message")
        return [], {}, str(detail or "No fue posible consultar los reportes.")
    data = response.get("data", {})
    return data.get("issues", []), data.get("summary", {}), None


def search_partner_media_issue_accounts(service, query):
    """Search provider-owned accounts that can be selected for a report."""
    service = str(service or "").strip().lower()
    query = str(query or "").strip()
    if service not in SERVICES:
        return [], "El servicio solicitado no es válido."
    if len(query) < 3:
        return [], "Escribe por lo menos 3 caracteres para buscar una cuenta."
    try:
        response = _authorized_request(
            "seller/account-issues/search/?"
            + urlencode({"platform": service, "q": query})
        )
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return [], _error_message(exc)
    if not response.get("success", False):
        detail = response.get("error", {})
        if isinstance(detail, dict):
            detail = detail.get("message")
        return [], str(detail or "No fue posible buscar la cuenta.")
    return response.get("data", {}).get("accounts", []), None


def get_partner_media_issue_account(service, count_id):
    """Validate one provider account immediately before reporting it."""
    service = str(service or "").strip().lower()
    if service not in SERVICES:
        return {}, "El servicio solicitado no es válido."
    try:
        response = _authorized_request(
            "seller/account-issues/account/?"
            + urlencode({"platform": service, "count_id": count_id})
        )
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return {}, _error_message(exc)
    if not response.get("success", False):
        detail = response.get("error", {})
        if isinstance(detail, dict):
            detail = detail.get("message")
        return {}, str(detail or "La cuenta no está disponible para reportarse.")
    return response.get("data", {}), None


def create_partner_media_issue(
    service,
    count_id,
    issue,
    file_name,
    file_content,
    file_content_type,
):
    """Send an account issue with the mandatory screenshot to the provider."""
    service = str(service or "").strip().lower()
    if service not in SERVICES:
        return {}, "El servicio solicitado no es válido."
    if not partner_api_configured():
        return {}, "La API Partner todavía no está configurada en Control."
    try:
        response = _authorized_multipart_request(
            "seller/account-issues/",
            {"platform": service, "count_id": count_id, "issue": issue},
            file_name,
            file_content,
            file_content_type,
        )
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return {}, _error_message(exc)
    if not response.get("success", False):
        detail = response.get("error", {})
        if isinstance(detail, dict):
            detail = detail.get("message")
        return {}, str(detail or "El proveedor no pudo registrar el reporte.")
    return response.get("data", {}), None
