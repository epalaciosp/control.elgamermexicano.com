from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0006_count_active"),
    ]

    operations = [
        migrations.CreateModel(
            name="WholesalePurchase",
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
                ("external_reference", models.CharField(max_length=64, verbose_name="Referencia externa")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Precio")),
                ("profiles_count", models.PositiveIntegerField(default=0, verbose_name="Perfiles")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="wholesale_purchases",
                        to="count.count",
                        verbose_name="Cuenta",
                    ),
                ),
                (
                    "bill",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="wholesale_purchase",
                        to="count.bill",
                        verbose_name="Factura",
                    ),
                ),
                (
                    "partner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchases",
                        to="count.wholesalepartner",
                        verbose_name="Mayorista",
                    ),
                ),
                (
                    "publication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchases",
                        to="count.wholesalepublication",
                        verbose_name="Publicación",
                    ),
                ),
            ],
            options={
                "verbose_name": "Compra mayorista",
                "verbose_name_plural": "Compras mayoristas",
                "ordering": ("-created_at", "-id"),
                "unique_together": {("partner", "external_reference")},
            },
        ),
    ]
