from django.db import models, transaction
from .validators import valid_extension, valid_image_extension
from user.models import Customer
from django.db.models.signals import post_save
from django.dispatch import receiver
from user.whatsapp_api import send_message
from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator, MinValueValidator
from count_admin_project.encrypted_fields import EncryptedCharField
import datetime
from decimal import Decimal


class Platform(models.Model):

    name = models.CharField(max_length=150, verbose_name="Nombre", default="")
    active = models.BooleanField(default=1, verbose_name="Activo?:")
    logo =  models.FileField(default="", upload_to='logos/', validators=[valid_image_extension])
    num_profiles = models.IntegerField(default=0, verbose_name="Número de perfiles")
    #have_plans = models.BooleanField(default=0, verbose_name="Tiene Planes?:")
    #price = models.FloatField(default=0, verbose_name="Precio")

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Plataforma'
        verbose_name_plural = 'Plataformas'

    @classmethod
    def get_my_platforms_with_counts(cls):

        platforms = cls.objects.all()
        for platform in platforms:
            have_counts = True if Profile.objects.filter(count__platform=platform, saled=0) else False
            if not have_counts:
                platforms = platforms.exclude(id=platform.id)
        return platforms

    @classmethod
    def get_num_of_profiles(cls, platform_id):

        platform = Platform.objects.filter(id=platform_id).first()
        return platform.num_profiles



#Planes de cada plataforma
#SubProduct(models.Model):
class Plan(models.Model):


    platform = models.ForeignKey(Platform, default=1, verbose_name="Plataforma", on_delete=models.CASCADE)
    name = models.CharField(max_length=150, verbose_name="Nombre", default="")
    num_profiles = models.IntegerField(default=0, verbose_name="Perfiles a vender")
    have_link = models.BooleanField(default=0, verbose_name="Se envia link?:")
    active = models.BooleanField(default=1, verbose_name="Activo?:")
    description = models.CharField(default="", max_length=250, verbose_name="Descripción")
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Precio de venta",
    )
    wholesale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Precio de mayoreo",
    )

    def __str__(self):
        return str(self.name)

    @classmethod
    def get_num_of_profiles(cls, plan_id):
        plan= cls.objects.filter(id=plan_id).first()
        return plan.num_profiles


class Country(models.Model):

    country = models.CharField(default="", max_length=100, verbose_name="Pais")
    iso =  models.CharField(default="", max_length=3, verbose_name="Iso")

    class Meta:
        verbose_name = 'Pais'
        verbose_name_plural = 'paises'
        ordering = ['country']

    def __str__(self):
        return self.country


class Count(models.Model):

    platform = models.ForeignKey(Platform, verbose_name="Plataforma", on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, blank=True, null=True, verbose_name="Plan", on_delete=models.CASCADE)
    country = models.ForeignKey(Country, default=1, verbose_name="Pais", on_delete=models.CASCADE)
    email = models.CharField(max_length=100, verbose_name="Email")
    link = EncryptedCharField(default="", max_length=2048, verbose_name="Link")
    password = EncryptedCharField(
        max_length=512,
        default="",
        validators=[MaxLengthValidator(50)],
        verbose_name="Contraseña de cuenta",
    )
    email_password = EncryptedCharField(
        max_length=512,
        default="",
        validators=[MaxLengthValidator(50)],
        verbose_name="Contraseña de correo",
    )
    date = models.DateTimeField(auto_now_add=True)
    date_limit = models.DateTimeField(blank=True,  null=True, verbose_name="Fecha de vencimiento",  auto_now_add=False)#Fecha de vencimiento de la cuenta
    active = models.BooleanField(default=True, verbose_name="Cuenta activa")
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Precio de venta de cuenta completa",
    )
    wholesale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Precio de mayoreo de cuenta completa",
    )

    class Meta:
        verbose_name = 'Cuenta'
        verbose_name_plural = 'Cuentas'

    def __str__(self):
        return str(self.email)

    @classmethod
    def complete_available(cls):
        """Accounts that can be sold whole without touching assigned profiles."""
        now = datetime.datetime.now(datetime.timezone.utc)
        active_sale = Sale.objects.filter(
            profile__count_id=models.OuterRef("pk"),
            renovated=False,
            cutted=False,
            date_limit__gte=now,
        )
        return cls.objects.filter(
            active=True,
            platform__active=True,
            date_limit__gte=now,
        ).annotate(
            total_profiles=models.Count("profile", distinct=True),
            available_profiles=models.Count(
                "profile",
                filter=models.Q(profile__saled=False),
                distinct=True,
            ),
            has_active_sale=models.Exists(active_sale),
        ).filter(
            total_profiles__gt=0,
            total_profiles=models.F("available_profiles"),
            has_active_sale=False,
        ).order_by("platform__name", "-date_limit", "id")


    def change_count_password(self, new_password):

        self.password  = new_password
        self.save()

    def change_email_password(self, new_password):
        self.email_password = new_password
        self.save()



class Promotion(models.Model):

    name = models.CharField(max_length=150, default="", verbose_name="Nombre")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    date_init = models.DateTimeField(verbose_name="Fecha de Inicio",  auto_now_add=False)
    date_finish = models.DateTimeField(verbose_name="Fecha de Finalización", auto_now_add=False)
    active = models.BooleanField(default=1, verbose_name="Activo?:")
    creater = models.ForeignKey(User, verbose_name="Creador", on_delete=models.CASCADE)
    image = models.FileField(default="", upload_to='promotions/', validators=[valid_image_extension])

    class Meta:
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'

    @classmethod
    def get_promotions_actives(cls):

        promotions_with_profiles = []
        now = datetime.datetime.now()
        promotions = cls.objects.filter(active=True, date_init__lt = now , date_finish__gt = now )
        for promotion in promotions:
            len_profiles = []
            promotion_platforms = PromotionPlatform.objects.filter(promotion=promotion)
            for promotion_platform in promotion_platforms:
                profiles = Profile.search_profiles_no_saled(promotion_platform.platform_id)

                len_profiles.append(len(profiles))
            if not 0 in len_profiles:
                promotions_with_profiles.append(promotion)
        return promotions_with_profiles



class PromotionPlatform(models.Model):

    promotion = models.ForeignKey(Promotion, verbose_name="Promoción", on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, verbose_name="Plataforma", on_delete=models.CASCADE)


class PromotionSale(models.Model):

    date = models.DateTimeField(verbose_name="Fecha", auto_now_add=True)
    promotion = models.ForeignKey(Promotion, verbose_name="Promoción", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, verbose_name="Plataforma", on_delete=models.CASCADE)

class Profile(models.Model):

    count = models.ForeignKey(Count, verbose_name="Cuenta", on_delete=models.CASCADE)
    profile = models.CharField(max_length=100, verbose_name="Perfil")
    pin = EncryptedCharField(
        max_length=255,
        validators=[MaxLengthValidator(5)],
        verbose_name="Pin",
        default="0",
    )
    saled = models.BooleanField(default=0, verbose_name="Vendida?:")

    #mixin
    #@receiver(post_save, sender=Count, dispatch_uid="creaction_of_profiles_by_count")
    def create_profiles(sender, instance, **kwargs):

        num_profiles = instance.platform.num_profiles
        for profile in range(num_profiles):
            Profile.objects.create(count=instance, profile=profile )
        return None

    def get_profiles_avaliable(sales, platform_id):

        from collections import Counter
        platform = Platform.objects.filter(id=platform_id).first()
        sales_profiles = list(sales.values_list('profile__profile', flat=True))
        repeats = []
        availables = []
        for x in range(1, int(platform.num_profiles) + 1):
            freq = Counter(sales_profiles).get(str(x))
            if freq:
                if freq > 1:
                    repeats.append(x)
            else:
                availables.append(x)
        have_avaliable = True if len(availables) > 0 else False

        return have_avaliable, availables, repeats

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

    @classmethod
    def search_profiles_no_saled(cls, platform_id):

        profiles = cls.objects.filter(saled=0, count__platform_id=platform_id)
        return profiles

    @classmethod
    def search_profiles_no_saled_by_plan(cls, plan_id):
        plan = Plan.objects.filter(id=plan_id, active=True).select_related("platform").first()
        if not plan:
            return cls.objects.none(), 0

        shared_inventory_platform = plan.platform.name.strip().casefold()
        if shared_inventory_platform == "iptv ibo pro player":
            profiles = cls.objects.filter(
                saled=0,
                count__platform=plan.platform,
            ).exclude(count__link="")
        elif shared_inventory_platform == "chatgpt plus":
            profiles = cls.objects.filter(
                saled=0,
                count__platform=plan.platform,
            )
        else:
            profiles = cls.objects.filter(saled=0, count__plan=plan)
        return profiles, plan.num_profiles

    @classmethod
    def change_password_to_perfile_message(cls, count, profile, now):

        if profile:
            profiles = [ profile ]
        else:
            profiles = cls.objects.filter(count=count)
        for profile in profiles:
            sale = Sale.search_customer_by_profile(profile, now)
            if sale:
                if profile.count.plan:
                    if not profile.count.plan.have_link:
                        message = f"Hola " + sale.bill.customer.name + ", Por motivos de seguridad la contraseña de tu cuenta ha sido cambiada: \n" \
                            f"Plataforma :" + count.platform.name + "\n" \
                            f"Correo : " + count.email + "\n" \
                            f"Nueva Contraseña " + count.password + "\n" \
                            f"Pin " + profile.pin + "\n" \
                            "Lamentamos el inconveniente, sigue disfrutando de tu servicio. \n" \
                            "Atte: El gamer Mx"
                    else:
                        message = f"Hola " + sale.bill.customer.name + ", Por motivos de seguridad la contraseña de tu cuenta ha sido cambiada: \n" \
                                  f"Plataforma :" + count.platform.name + "\n" \
                                  f"link : " + count.link + "\n" \
                                  f"Perfil " + profile.profile + "\n" \
                                  "Lamentamos el inconveniente, sigue disfrutando de tu servicio. \n" \
                                  "Atte: El gamer Mx"
                else:
                    message = f"Hola " + sale.bill.customer.name + ", Por motivos de seguridad la contraseña de tu cuenta ha sido cambiada: \n" \
                              f"Plataforma :" + count.platform.name + "\n" \
                              f"link : " + count.link + "\n" \
                              f"Perfil " + profile.profile + "\n" \
                              "Lamentamos el inconveniente, sigue disfrutando de tu servicio. \n" \
                              "Atte: El gamer Mx"

                customer_number = str(sale.bill.customer.phone)
                send_message(customer_number, message)
class Price(models.Model):

    platform = models.ForeignKey(Platform, verbose_name="Plataforma", on_delete=models.CASCADE)
    num_profiles = models.PositiveIntegerField( verbose_name="Número de perfiles")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio")

    class Meta:
        verbose_name = 'Precio'
        verbose_name_plural = 'Precios'


class Bill(models.Model):

    date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, verbose_name="Cliente", on_delete=models.CASCADE)
    saler = models.ForeignKey(User, verbose_name="Vendedor", on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Precio")

    @classmethod
    def GetInterdatesBills(cls, user, initial_date, final_date):

        initial_date = datetime.datetime.strptime(initial_date, '%Y-%m-%d')
        final_date = datetime.datetime.strptime(final_date, '%Y-%m-%d')
        initial_date = initial_date + datetime.timedelta(hours=5)
        final_date = final_date + datetime.timedelta(hours=29)
        bills = cls.objects.filter(saler=user, date__range=[initial_date, final_date]).order_by('-date')
        return bills

class Sale(models.Model):

    date = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name="Perfil")
    months = models.PositiveIntegerField(default=1)
    date_limit = models.DateTimeField(verbose_name="Fecha de vencimiento", blank=True, null=True, auto_now_add=False)
    bill = models.ForeignKey(Bill, verbose_name="Factura", on_delete=models.CASCADE)
    renovated = models.BooleanField(default=0, verbose_name="Renovada:")
    cutted = models.BooleanField(default=0, verbose_name="Cortado:")
    device_mac = models.CharField(max_length=17, blank=True, default="", verbose_name="MAC address")
    device_key = EncryptedCharField(max_length=512, blank=True, default="", verbose_name="Clave del dispositivo")

    @property
    def is_ibo_player(self):
        return self.profile.count.platform.name.strip().casefold() == "iptv ibo pro player"

    @property
    def access_identifier(self):
        return self.device_mac if self.is_ibo_player else self.profile.count.email

    @property
    def access_password(self):
        return self.device_key if self.is_ibo_player else self.profile.count.password

    @classmethod
    def search_customer_by_profile(cls, profile, now):
        sale = cls.objects.filter(profile=profile, date_limit__gte=now).last()
        return sale

    @classmethod
    def GetInterdatesSales(cls, user, initial_date, final_date):

        initial_date = datetime.datetime.strptime(initial_date, '%Y-%m-%d')
        final_date = datetime.datetime.strptime(final_date, '%Y-%m-%d')
        initial_date = initial_date + datetime.timedelta(hours=5)
        final_date = final_date + datetime.timedelta(hours=29)
        sales = cls.objects.filter(bill__saler=user, date__range=[initial_date, final_date]).order_by('-date')
        return sales

    def set_renovation(self, saler, months,  CalculateDateLimit):

        date_limit = CalculateDateLimit(self.date_limit, months)
        bill = Bill.objects.create(customer=self.bill.customer, saler=saler, total=total)
        self.objects.create(
                            months=months,
                            date_limit=date_limit,
                            bill=saler)

    def cancel_sale(self):
        """Cancel the complete customer/profile service without deleting history."""
        return self.cut_customer_profile_history()

    def cut_customer_profile_history(self):
        """Cut every sale in this customer's history for the same profile."""
        customer_id = self.bill.customer_id

        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(pk=self.profile_id)
            sales = Sale.objects.select_for_update().filter(
                profile_id=self.profile_id,
                bill__customer_id=customer_id,
                cutted=False,
            )
            updated_count = sales.update(cutted=True)

            profile_in_use = Sale.objects.filter(
                profile_id=self.profile_id,
                renovated=False,
                cutted=False,
            ).exists()
            profile.saled = profile_in_use
            profile.save(update_fields=["saled"])

        return updated_count, not profile_in_use

    def change_count_password(self, new_password):

        self.count.password  = new_password
        self.count.save()


class WholesalePartner(models.Model):
    """Cliente mayorista autorizado para consultar inventario publicado."""

    customer = models.OneToOneField(
        Customer,
        related_name="wholesale_partner",
        verbose_name="Cliente",
        on_delete=models.PROTECT,
    )
    username = models.CharField(max_length=150, unique=True, verbose_name="Usuario")
    external_user_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        unique=True,
        verbose_name="ID externo",
    )
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("username",)
        verbose_name = "Cliente mayorista"
        verbose_name_plural = "Clientes mayoristas"

    def __str__(self):
        return self.username


class WholesalePublication(models.Model):
    """Plan y precio que Control publica para un cliente mayorista."""

    partner = models.ForeignKey(
        WholesalePartner,
        related_name="publications",
        verbose_name="Mayorista",
        on_delete=models.CASCADE,
    )
    plan = models.ForeignKey(
        Plan,
        related_name="wholesale_publications",
        verbose_name="Plan",
        on_delete=models.PROTECT,
    )
    wholesale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Precio mayorista",
    )
    stock_limit = models.PositiveIntegerField(
        default=0,
        verbose_name="Límite de inventario",
        help_text="Use 0 para publicar toda la disponibilidad real del plan.",
    )
    catalog_title = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Título en catálogo",
        help_text="Si se deja vacío se usa el nombre de la plataforma.",
    )
    catalog_description = models.CharField(
        max_length=300,
        blank=True,
        default="",
        verbose_name="Descripción en catálogo",
    )
    catalog_image = models.ImageField(
        upload_to="wholesale/catalog/",
        blank=True,
        null=True,
        validators=[valid_image_extension],
        verbose_name="Imagen del catálogo",
        help_text="Si se deja vacía se usa el logo de la plataforma.",
    )
    featured = models.BooleanField(default=False, verbose_name="Destacado")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    active = models.BooleanField(default=True, verbose_name="Publicado")
    created_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="wholesale_publications_created",
        verbose_name="Creado por",
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("partner__username", "plan__platform__name", "plan__name")
        unique_together = (("partner", "plan"),)
        verbose_name = "Publicación mayorista"
        verbose_name_plural = "Publicaciones mayoristas"

    def __str__(self):
        return f"{self.partner.username} · {self.plan.platform.name} · {self.plan.name}"

    @classmethod
    def complete_accounts_for_plan(cls, plan):
        """Return active accounts whose complete profile capacity is available."""
        if not plan or not plan.num_profiles:
            return Count.objects.none()

        return Count.complete_available().filter(
            plan=plan,
            total_profiles=plan.num_profiles,
        ).order_by("-date_limit", "id")

    @property
    def available_units(self):
        units = self.complete_accounts_for_plan(self.plan).count()
        if self.stock_limit:
            units = min(units, self.stock_limit)
        return units

    @property
    def next_account_days(self):
        account = self.complete_accounts_for_plan(self.plan).first()
        if not account or not account.date_limit:
            return 0
        today = datetime.datetime.now(datetime.timezone.utc).date()
        return max((account.date_limit.date() - today).days, 0)

    @property
    def display_title(self):
        return self.catalog_title.strip() or self.plan.platform.name

    @property
    def display_description(self):
        return self.catalog_description.strip() or self.plan.description


class WholesalePurchase(models.Model):
    """Idempotent purchase of a full account or plan by a wholesaler."""

    ACCOUNT = "account"
    PLAN = "plan"
    PURCHASE_TYPE_CHOICES = (
        (ACCOUNT, "Cuenta completa"),
        (PLAN, "Plan o perfil"),
    )

    partner = models.ForeignKey(
        WholesalePartner,
        related_name="purchases",
        verbose_name="Mayorista",
        on_delete=models.PROTECT,
    )
    publication = models.ForeignKey(
        WholesalePublication,
        related_name="purchases",
        verbose_name="Publicación",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    account = models.ForeignKey(
        Count,
        related_name="wholesale_purchases",
        verbose_name="Cuenta",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    plan = models.ForeignKey(
        Plan,
        related_name="wholesale_purchases",
        verbose_name="Plan",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    bill = models.OneToOneField(
        Bill,
        related_name="wholesale_purchase",
        verbose_name="Factura",
        on_delete=models.PROTECT,
    )
    external_reference = models.CharField(
        max_length=64,
        verbose_name="Referencia externa",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio",
    )
    profiles_count = models.PositiveIntegerField(default=0, verbose_name="Perfiles")
    purchase_type = models.CharField(
        max_length=12,
        choices=PURCHASE_TYPE_CHOICES,
        default=ACCOUNT,
        verbose_name="Tipo de compra",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        unique_together = (("partner", "external_reference"),)
        verbose_name = "Compra mayorista"
        verbose_name_plural = "Compras mayoristas"

    def __str__(self):
        if self.account_id:
            product = self.account.platform.name
        elif self.plan_id:
            product = self.plan.platform.name + " · " + self.plan.name
        else:
            product = "Compra"
        return f"{self.partner.username} · {product} · {self.external_reference}"


class WholesaleSlide(models.Model):
    """Anuncio que Control publica en el dashboard de MyPlataforma."""

    title = models.CharField(max_length=150, verbose_name="Título")
    subtitle = models.CharField(
        max_length=300,
        blank=True,
        default="",
        verbose_name="Descripción",
    )
    image = models.ImageField(
        upload_to="wholesale/slides/",
        validators=[valid_image_extension],
        verbose_name="Imagen",
    )
    button_text = models.CharField(
        max_length=60,
        blank=True,
        default="",
        verbose_name="Texto del botón",
    )
    button_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Enlace del botón",
    )
    active = models.BooleanField(default=True, verbose_name="Publicado")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    starts_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Publicar desde",
    )
    ends_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Publicar hasta",
    )
    created_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="wholesale_slides_created",
        verbose_name="Creado por",
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "-updated_at")
        permissions = (
            ("manage_myplataforma", "Puede administrar MyPlataforma"),
            (
                "manage_wholesale_customers",
                "Puede administrar clientes mayoristas",
            ),
            (
                "manage_wholesale_slides",
                "Puede administrar anuncios de MyPlataforma",
            ),
        )
        verbose_name = "Anuncio de MyPlataforma"
        verbose_name_plural = "Anuncios de MyPlataforma"

    def __str__(self):
        return self.title



def sale_profile(self, profile, months, date_limit, bill, device_mac="", device_key=""):

    profile_saled = Sale.objects.create(
                        profile = profile,
                        months = months,
                        date_limit = date_limit,
                        bill=bill,
                        device_mac=device_mac,
                        device_key=device_key,
                        )
    profile.saled = True
    profile.save()
    return profile_saled

User.add_to_class("sale_profile", sale_profile)
