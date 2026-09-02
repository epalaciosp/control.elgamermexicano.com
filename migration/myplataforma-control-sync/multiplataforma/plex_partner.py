"""Read-only client for the Multiplataforma Partner API.

Credentials live only in the server environment. Purchasing is intentionally
not exposed until the fixed KVM4 IP has been approved by the provider.
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.cache import cache


BASE_URL = os.environ.get(
    "MULTIPLATAFORMA_PARTNER_API_URL",
    "https://multiplataforma.co/api/partner/v1/",
).rstrip("/") + "/"
USERNAME = os.environ.get("MULTIPLATAFORMA_PARTNER_USERNAME", "").strip()
PASSWORD = os.environ.get("MULTIPLATAFORMA_PARTNER_PASSWORD", "")


def plex_api_configured():
    return bool(USERNAME and PASSWORD)


def _request_json(path, method="GET", payload=None, token=""):
    body = None
    headers = {"Accept": "application/json", "User-Agent": "MyPlataforma-Plex/1.0"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(BASE_URL + path.lstrip("/"), data=body, headers=headers, method=method)
    with urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def _access_token():
    token = cache.get("multiplataforma_partner_access_token")
    if token:
        return token
    payload = _request_json(
        "auth/token/",
        method="POST",
        payload={"username": USERNAME, "password": PASSWORD},
    )
    token = payload.get("data", {}).get("tokens", {}).get("access", "")
    if token:
        cache.set("multiplataforma_partner_access_token", token, 240)
    return token


def get_plex_market():
    if not plex_api_configured():
        return [], "Pendiente de credenciales e IP autorizada por Multiplataforma."
    try:
        token = _access_token()
        if not token:
            return [], "La API de Plex no devolvió un token válido."
        payload = _request_json("plex/market/", token=token)
    except HTTPError as exc:
        if exc.code == 403:
            return [], "La IP fija del KVM4 todavía no está autorizada para la API de Plex."
        return [], "La API de Plex respondió con error {}.".format(exc.code)
    except (URLError, TimeoutError, ValueError):
        return [], "No fue posible consultar la API de Plex en este momento."

    data = payload.get("data", {})
    plans = data.get("plans", data if isinstance(data, list) else [])
    return plans if isinstance(plans, list) else [], None
