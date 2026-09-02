from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


def seed_catalog_prices(apps, schema_editor):
    Plan = apps.get_model("count", "Plan")
    Count = apps.get_model("count", "Count")
    Price = apps.get_model("count", "Price")
    Profile = apps.get_model("count", "Profile")
    WholesalePublication = apps.get_model("count", "WholesalePublication")

    for plan in Plan.objects.select_related("platform"):
        legacy = Price.objects.filter(
            platform_id=plan.platform_id,
            num_profiles=plan.num_profiles,
        ).order_by("id").first()
        sale_price = legacy.price if legacy else Decimal("0")
        publication = WholesalePublication.objects.filter(
            plan_id=plan.id,
            active=True,
        ).order_by("wholesale_price", "id").first()
        wholesale_price = publication.wholesale_price if publication else Decimal("0")
        Plan.objects.filter(pk=plan.pk).update(
            sale_price=sale_price,
            wholesale_price=wholesale_price,
        )

    for account in Count.objects.select_related("plan", "platform"):
        profile_count = Profile.objects.filter(count_id=account.id).count()
        legacy = Price.objects.filter(
            platform_id=account.platform_id,
            num_profiles=profile_count,
        ).order_by("id").first()
        sale_price = legacy.price if legacy else Decimal("0")
        wholesale_price = (
            account.plan.wholesale_price
            if account.plan_id and account.plan.wholesale_price
            else Decimal("0")
        )
        Count.objects.filter(pk=account.pk).update(
            sale_price=sale_price,
            wholesale_price=wholesale_price,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0007_wholesale_purchase"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="sale_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0"))], verbose_name="Precio de venta"),
        ),
        migrations.AddField(
            model_name="plan",
            name="wholesale_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0"))], verbose_name="Precio de mayoreo"),
        ),
        migrations.AddField(
            model_name="count",
            name="sale_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0"))], verbose_name="Precio de venta de cuenta completa"),
        ),
        migrations.AddField(
            model_name="count",
            name="wholesale_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0"))], verbose_name="Precio de mayoreo de cuenta completa"),
        ),
        migrations.AddField(
            model_name="wholesalepurchase",
            name="plan",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="wholesale_purchases", to="count.plan", verbose_name="Plan"),
        ),
        migrations.AddField(
            model_name="wholesalepurchase",
            name="purchase_type",
            field=models.CharField(choices=[("account", "Cuenta completa"), ("plan", "Plan o perfil")], default="account", max_length=12, verbose_name="Tipo de compra"),
        ),
        migrations.AlterField(
            model_name="wholesalepurchase",
            name="account",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="wholesale_purchases", to="count.count", verbose_name="Cuenta"),
        ),
        migrations.AlterField(
            model_name="wholesalepurchase",
            name="publication",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="purchases", to="count.wholesalepublication", verbose_name="Publicación"),
        ),
        migrations.RunPython(seed_catalog_prices, migrations.RunPython.noop),
    ]
