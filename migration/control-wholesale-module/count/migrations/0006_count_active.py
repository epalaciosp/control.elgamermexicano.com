from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0005_wholesale_catalog_and_slides"),
    ]

    operations = [
        migrations.AddField(
            model_name="count",
            name="active",
            field=models.BooleanField(default=True, verbose_name="Cuenta activa"),
        ),
    ]
