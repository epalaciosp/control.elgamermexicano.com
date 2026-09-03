from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0012_count_profile_sale_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="PartnerMediaPrice",
            fields=[
                (
                    "id",
                    models.AutoField(
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
                (
                    "external_plan_id",
                    models.CharField(max_length=100, verbose_name="ID del plan"),
                ),
                ("name", models.CharField(max_length=200, verbose_name="Plan")),
                (
                    "connections",
                    models.PositiveIntegerField(default=1, verbose_name="Dispositivos"),
                ),
                (
                    "duration",
                    models.CharField(blank=True, default="", max_length=80, verbose_name="Duración"),
                ),
                ("with_tv", models.BooleanField(default=False, verbose_name="Incluye TV")),
                (
                    "currency_prefix",
                    models.CharField(blank=True, default="MXN", max_length=12),
                ),
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
                (
                    "sale_price",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                        validators=[MinValueValidator(Decimal("0"))],
                        verbose_name="Precio de venta",
                    ),
                ),
                ("active", models.BooleanField(default=False, verbose_name="Publicado")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Precio API de MyPlataforma",
                "verbose_name_plural": "Precios API de MyPlataforma",
                "ordering": ("service", "with_tv", "provider_cost", "name"),
                "permissions": (
                    (
                        "manage_partner_media_prices",
                        "Puede administrar precios API de MyPlataforma",
                    ),
                ),
                "unique_together": {("service", "external_plan_id", "with_tv")},
            },
        ),
    ]
