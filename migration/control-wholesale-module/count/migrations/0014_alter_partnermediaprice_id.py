from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0013_partner_media_prices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="partnermediaprice",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
    ]
