from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


def seed_wholesale_partners(apps, schema_editor):
    Customer = apps.get_model("user", "Customer")
    WholesalePartner = apps.get_model("count", "WholesalePartner")

    partners = (
        (1716, "Yehoshua", 29, "Yehoshua"),
        (2276, "arojas7", 51, "arojas"),
    )
    for customer_id, username, external_user_id, name_fragment in partners:
        customer = Customer.objects.filter(pk=customer_id).first()
        if customer is None:
            customer = Customer.objects.filter(
                name__icontains=name_fragment
            ).order_by("id").first()
        if customer is None:
            continue

        WholesalePartner.objects.update_or_create(
            username=username,
            defaults={
                "customer_id": customer.pk,
                "external_user_id": external_user_id,
                "active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0003_ibo_player_inventory"),
    ]

    operations = [
        migrations.CreateModel(
            name="WholesalePartner",
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
                ("username", models.CharField(max_length=150, unique=True, verbose_name="Usuario")),
                (
                    "external_user_id",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        unique=True,
                        verbose_name="ID externo",
                    ),
                ),
                ("active", models.BooleanField(default=True, verbose_name="Activo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="wholesale_partner",
                        to="user.customer",
                        verbose_name="Cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Cliente mayorista",
                "verbose_name_plural": "Clientes mayoristas",
                "ordering": ("username",),
            },
        ),
        migrations.CreateModel(
            name="WholesalePublication",
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
                    "wholesale_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[MinValueValidator(Decimal("0.01"))],
                        verbose_name="Precio mayorista",
                    ),
                ),
                (
                    "stock_limit",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Use 0 para publicar toda la disponibilidad real del plan.",
                        verbose_name="Límite de inventario",
                    ),
                ),
                ("active", models.BooleanField(default=True, verbose_name="Publicado")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="wholesale_publications_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Creado por",
                    ),
                ),
                (
                    "partner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="publications",
                        to="count.wholesalepartner",
                        verbose_name="Mayorista",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="wholesale_publications",
                        to="count.plan",
                        verbose_name="Plan",
                    ),
                ),
            ],
            options={
                "verbose_name": "Publicación mayorista",
                "verbose_name_plural": "Publicaciones mayoristas",
                "ordering": ("partner__username", "plan__platform__name", "plan__name"),
                "unique_together": {("partner", "plan")},
            },
        ),
        migrations.RunPython(seed_wholesale_partners, migrations.RunPython.noop),
    ]
