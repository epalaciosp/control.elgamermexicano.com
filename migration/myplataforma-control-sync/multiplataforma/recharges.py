"""Secure balance recharges for MyPlataforma.

Mercado Pago remains the source of truth for payment state.  A browser return
never credits balance; only a signed webhook followed by a server-side payment
lookup can do that.
"""

import hashlib
import hmac
import json
import os
import secrets
import uuid
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from .models import MoneysSaler


MERCADO_PAGO_API = "https://api.mercadopago.com"


class RechargeOrder(models.Model):
    METHOD_MERCADO_PAGO = "mercadopago"
    METHOD_BANK = "bank"
    METHOD_BINANCE = "binance"
    METHOD_CHOICES = (
        (METHOD_MERCADO_PAGO, "Tarjeta o SPEI"),
        (METHOD_BANK, "Transferencia manual"),
        (METHOD_BINANCE, "Binance Pay"),
    )

    STATUS_PENDING = "pending"
    STATUS_REVIEW = "review"
    STATUS_PAID = "paid"
    STATUS_REJECTED = "rejected"
    STATUS_EXPIRED = "expired"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pendiente"),
        (STATUS_REVIEW, "En revisión"),
        (STATUS_PAID, "Pagada"),
        (STATUS_REJECTED, "Rechazada"),
        (STATUS_EXPIRED, "Vencida"),
        (STATUS_REFUNDED, "Reembolsada"),
    )

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recharge_orders",
    )
    amount_mxn = models.PositiveIntegerField()
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    provider_order_id = models.CharField(max_length=120, blank=True, db_index=True)
    provider_payment_id = models.CharField(max_length=120, blank=True, db_index=True)
    provider_status = models.CharField(max_length=80, blank=True)
    checkout_url = models.URLField(max_length=800, blank=True)
    money_movement = models.OneToOneField(
        MoneysSaler,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="recharge_order",
    )
    credited_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "multiplataforma"
        db_table = "multiplataforma_rechargeorder"
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(fields=("user", "status"), name="recharge_user_status_idx"),
        )

    def __str__(self):
        return "Recarga {} por ${}".format(self.public_id, self.amount_mxn)

    @classmethod
    def credit_once(cls, order_id):
        """Credit a verified paid order exactly once, even under concurrency."""
        with transaction.atomic():
            order = cls.objects.select_for_update().select_related("user").get(pk=order_id)
            if order.status != cls.STATUS_PAID or order.credited_at:
                return False

            # Lock the user and the latest ledger entry so purchases and
            # simultaneous webhook retries cannot overwrite one another.
            User.objects.select_for_update().get(pk=order.user_id)
            latest = (
                MoneysSaler.objects.select_for_update()
                .filter(saler_id=order.user_id)
                .order_by("-date", "-id")
                .first()
            )
            current_balance = int(latest.money or 0) if latest else 0
            movement = MoneysSaler.objects.create(
                saler_id=order.user_id,
                money=current_balance + order.amount_mxn,
                transaction_money=order.amount_mxn,
                detail="Recarga Mercado Pago · {}".format(order.public_id),
            )
            order.money_movement = movement
            order.credited_at = timezone.now()
            order.save(update_fields=("money_movement", "credited_at", "updated_at"))
            return True


class RechargeWebhookEvent(models.Model):
    provider = models.CharField(max_length=24)
    event_hash = models.CharField(max_length=64, unique=True)
    external_event_id = models.CharField(max_length=160, blank=True)
    processed = models.BooleanField(default=False)
    response_code = models.PositiveSmallIntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "multiplataforma"
        db_table = "multiplataforma_rechargewebhookevent"
        ordering = ("-created_at", "-id")


def mercado_pago_configured():
    return bool(
        os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "").strip()
        and os.environ.get("MERCADOPAGO_WEBHOOK_SECRET", "").strip()
    )


def mercado_pago_environment():
    """Return the checkout environment that matches the configured token.

    Mercado Pago production tokens use the ``APP_USR-`` prefix and test
    tokens use ``TEST-``.  The credential is the source of truth because
    sending a production preference to the sandbox (or the reverse) makes
    Checkout Pro reject the payer as a test/production mismatch.

    ``MERCADOPAGO_MODE`` remains as a fallback for legacy token formats.
    """
    token = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "").strip().upper()
    if token.startswith("APP_USR-"):
        return "production"
    if token.startswith("TEST-"):
        return "test"

    mode = os.environ.get("MERCADOPAGO_MODE", "test").strip().lower()
    return "production" if mode == "production" else "test"


def recharge_limits():
    try:
        minimum = max(100, int(os.environ.get("RECHARGE_MIN_MXN", "100")))
        maximum = min(50000, int(os.environ.get("RECHARGE_MAX_MXN", "10000")))
    except ValueError:
        minimum, maximum = 100, 10000
    if maximum < minimum:
        maximum = minimum
    return minimum, maximum


def _api_json(url, method="GET", payload=None):
    token = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Mercado Pago no está configurado.")
    body = None
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "MyPlataforma-Recharges/1.0",
    }
    if payload is not None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["X-Idempotency-Key"] = secrets.token_hex(16)
    request = Request(url, data=body, method=method, headers=headers)
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("message")
        except (ValueError, UnicodeDecodeError):
            detail = None
        raise RuntimeError(detail or "Mercado Pago rechazó la solicitud.") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("No fue posible comunicarse con Mercado Pago.") from exc


def create_mercado_pago_checkout(order, request):
    base_url = "{}://{}".format(
        "https" if request.is_secure() else "http",
        request.get_host(),
    )
    return_path = reverse("recharge-center")
    payload = {
        "items": [{
            "id": str(order.public_id),
            "title": "Recarga de saldo MyPlataforma",
            "description": "Saldo para compras mayoristas",
            "currency_id": "MXN",
            "quantity": 1,
            "unit_price": order.amount_mxn,
        }],
        "external_reference": str(order.public_id),
        "back_urls": {
            "success": base_url + return_path + "?payment=success",
            "pending": base_url + return_path + "?payment=pending",
            "failure": base_url + return_path + "?payment=failure",
        },
        "auto_return": "approved",
        "notification_url": base_url + reverse("mercadopago-recharge-webhook"),
        "statement_descriptor": "MYPLATAFORMA",
    }
    result = _api_json(
        MERCADO_PAGO_API + "/checkout/preferences",
        method="POST",
        payload=payload,
    )
    if mercado_pago_environment() == "production":
        checkout_url = result.get("init_point")
    else:
        checkout_url = result.get("sandbox_init_point")
    if not result.get("id") or not checkout_url:
        raise RuntimeError("Mercado Pago no devolvió un enlace de pago.")
    order.provider_order_id = str(result["id"])
    order.checkout_url = checkout_url
    order.save(update_fields=("provider_order_id", "checkout_url", "updated_at"))
    return checkout_url


def validate_mercado_pago_signature(request, data_id):
    secret = os.environ.get("MERCADOPAGO_WEBHOOK_SECRET", "").strip()
    signature = request.headers.get("x-signature", "")
    request_id = request.headers.get("x-request-id", "")
    parts = {}
    for part in signature.split(","):
        key, separator, value = part.strip().partition("=")
        if separator:
            parts[key] = value
    timestamp = parts.get("ts", "")
    received = parts.get("v1", "")
    if not all((secret, data_id, request_id, timestamp, received)):
        return False
    manifest = "id:{};request-id:{};ts:{};".format(
        str(data_id).lower(),
        request_id,
        timestamp,
    )
    expected = hmac.new(
        secret.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, received)


def fetch_mercado_pago_payment(payment_id):
    if not str(payment_id).isdigit():
        raise RuntimeError("Identificador de pago inválido.")
    return _api_json(MERCADO_PAGO_API + "/v1/payments/" + str(payment_id))


def verify_payment_for_order(payment, order):
    try:
        amount = Decimal(str(payment.get("transaction_amount")))
    except (InvalidOperation, TypeError, ValueError):
        return False
    return bool(
        payment.get("status") == "approved"
        and payment.get("currency_id") == "MXN"
        and str(payment.get("external_reference")) == str(order.public_id)
        and amount == Decimal(order.amount_mxn)
    )


def webhook_event_hash(raw_body, signature, request_id):
    return hashlib.sha256(
        raw_body + signature.encode("utf-8") + request_id.encode("utf-8")
    ).hexdigest()
