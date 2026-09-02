from django.core.validators import MinValueValidator
from django.db import migrations, models
from decimal import Decimal


def create_ibo_two_device_plan(apps, schema_editor):
    Platform = apps.get_model("count", "Platform")
    Plan = apps.get_model("count", "Plan")

    platform = Platform.objects.filter(name__iexact="IPTV IBO Pro Player").first()
    if not platform:
        return
    if Plan.objects.filter(platform=platform, num_profiles=2).exists():
        return
    Plan.objects.create(
        platform=platform,
        name="2 DISPOSITIVOS",
        num_profiles=2,
        have_link=True,
        active=True,
        description="Venta de dos dispositivos de una misma lista IBO.",
        sale_price=Decimal("0"),
        wholesale_price=Decimal("0"),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0011_granular_myplataforma_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="count",
            name="profile_sale_price",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
                validators=[MinValueValidator(Decimal("0"))],
                verbose_name="Precio de venta por perfil",
            ),
        ),
        migrations.RunPython(
            create_ibo_two_device_plan,
            migrations.RunPython.noop,
        ),
    ]
