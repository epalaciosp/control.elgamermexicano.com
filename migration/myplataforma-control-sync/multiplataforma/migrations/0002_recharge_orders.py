import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("multiplataforma", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RechargeOrder",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("amount_mxn", models.PositiveIntegerField()),
                ("method", models.CharField(choices=[("mercadopago", "Tarjeta o SPEI"), ("bank", "Transferencia manual"), ("binance", "Binance Pay")], max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pendiente"), ("review", "En revisión"), ("paid", "Pagada"), ("rejected", "Rechazada"), ("expired", "Vencida"), ("refunded", "Reembolsada")], default="pending", max_length=16)),
                ("provider_order_id", models.CharField(blank=True, db_index=True, max_length=120)),
                ("provider_payment_id", models.CharField(blank=True, db_index=True, max_length=120)),
                ("provider_status", models.CharField(blank=True, max_length=80)),
                ("checkout_url", models.URLField(blank=True, max_length=800)),
                ("credited_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("money_movement", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="recharge_order", to="multiplataforma.moneyssaler")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recharge_orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "multiplataforma_rechargeorder", "ordering": ("-created_at", "-id")},
        ),
        migrations.AddIndex(
            model_name="rechargeorder",
            index=models.Index(fields=["user", "status"], name="recharge_user_status_idx"),
        ),
        migrations.CreateModel(
            name="RechargeWebhookEvent",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(max_length=24)),
                ("event_hash", models.CharField(max_length=64, unique=True)),
                ("external_event_id", models.CharField(blank=True, max_length=160)),
                ("processed", models.BooleanField(default=False)),
                ("response_code", models.PositiveSmallIntegerField(default=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "multiplataforma_rechargewebhookevent", "ordering": ("-created_at", "-id")},
        ),
    ]
