from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("count", "0014_alter_partnermediaprice_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="PartnerMediaAccount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "service",
                    models.CharField(
                        choices=(
                            ("plex", "Plex"),
                            ("emby", "Emby"),
                            ("jellyfin", "Jellyfin"),
                        ),
                        max_length=20,
                        verbose_name="Servicio",
                    ),
                ),
                ("external_account_id", models.CharField(max_length=100, verbose_name="ID externo")),
                ("external_plan_id", models.CharField(max_length=100, verbose_name="ID del plan")),
                ("plan_name", models.CharField(max_length=200, verbose_name="Plan")),
                ("connections", models.PositiveIntegerField(default=1, verbose_name="Dispositivos")),
                ("with_tv", models.BooleanField(default=False, verbose_name="Incluye TV")),
                ("customer_name", models.CharField(max_length=200, verbose_name="Cliente")),
                ("access_identifier", models.CharField(max_length=254, verbose_name="Correo o usuario")),
                ("access_password", models.CharField(max_length=255, verbose_name="Contraseña")),
                (
                    "provider_cost",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                        validators=[MinValueValidator(Decimal("0"))],
                        verbose_name="Costo proveedor",
                    ),
                ),
                ("currency_prefix", models.CharField(blank=True, default="MXN", max_length=12)),
                ("date_start", models.DateTimeField(blank=True, null=True, verbose_name="Inicio")),
                ("date_end", models.DateTimeField(blank=True, null=True, verbose_name="Vencimiento")),
                ("server_url", models.URLField(blank=True, default="", max_length=500)),
                ("activation_label", models.CharField(blank=True, default="", max_length=200)),
                ("instructions", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "purchased_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="partner_media_accounts_purchased",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Generado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Cuenta multimedia del proveedor",
                "verbose_name_plural": "Cuentas multimedia del proveedor",
                "ordering": ("-created_at", "-id"),
                "permissions": (
                    ("purchase_partner_plex", "Puede generar cuentas Plex a costo"),
                    ("purchase_partner_emby", "Puede generar cuentas Emby a costo"),
                    ("purchase_partner_jellyfin", "Puede generar cuentas Jellyfin a costo"),
                ),
                "unique_together": {("service", "external_account_id")},
            },
        ),
    ]
