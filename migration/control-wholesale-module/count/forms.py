from django import forms
from .models import (
    Sale,
    Platform,
    Plan,
    Count,
    Promotion,
    Country,
    WholesalePartner,
    WholesalePublication,
    WholesaleSlide,
)
from .libraries import is_chatgpt_plus_platform, normalize_ibo_device_identifier

from datetime import date

class SaleForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        self.fields['platform'] = forms.ModelChoiceField(queryset=Platform.get_my_platforms_with_counts(), required=True, label="Plataforma")
        self.fields['months'] = forms.IntegerField(min_value=1 ,label="Meses", required=True)



class RenovationForm(forms.Form):


    months = forms.IntegerField(label="Meses", required=True, widget= forms.NumberInput(attrs={'placeholder':'Ingrese los meses', 'min':'1'}))


class GetInterDatesForm(forms.Form):

    def __init__(self, *args, **kwargs):

        super(GetInterDatesForm, self).__init__(*args, **kwargs)
        self.fields['init_date'] = forms.DateField(widget=forms.DateInput(
            attrs={'type': 'date', 'placeholder': 'Digite la fecha inicial', 'data-date-format': 'YYYY/MMMM/DD',
                   'value': date.today()}))
        self.fields['final_date'] = forms.DateField(widget=forms.DateInput(
            attrs={'type': 'date', 'placeholder': 'Digite la fecha final', 'data-date-format': 'YYYY/MMMM/DD',
                   'value': date.today()}))

    class Meta:
        fields = ('init_date', 'final_date')

class CountForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(CountForm, self).__init__(*args, **kwargs)
        platforms = Platform.objects.filter(active=True)
        self.fields['platform'] = forms.ModelChoiceField(queryset=platforms, empty_label='Selecciones la plataforma',
                                                      label="Plataforma")
        countries = Country.objects.all()
        self.fields['country'] = forms.ModelChoiceField(queryset=countries, empty_label='Selecciones el pais',
                                                         label="Pais")
        self.fields['country'].initial = 1

        self.fields['date_limit'] = forms.DateField(label="Fecha de vencimiento",  widget=forms.DateInput(
            attrs={'type': 'date', 'placeholder': 'Digite la fecha de vencimiento', 'data-date-format': 'YYYY/MMMM/DD',
                   'value': date.today()}))

    email = forms.CharField(required=True)
    password = forms.CharField(required=True, label="Contraseña de cuenta")
    email_password = forms.CharField(required=True, label="Contraseña de email")
    sale_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        label="Precio de venta de cuenta completa",
    )
    profile_sale_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        label="Precio de venta por perfil",
    )
    wholesale_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        label="Precio de mayoreo de cuenta completa",
    )



    def save(self, commit=True):

        instance = super().save(commit=False)
        super(CountForm, self).save(*args, **kwargs)


class CountUpdateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CountUpdateForm, self).__init__(*args, **kwargs)
        self.fields['platform'].widget.attrs['disabled'] = 'disabled'
        self.fields['plan'].required = False
        if self.instance and self.instance.platform_id:
            self.fields['plan'].queryset = Plan.objects.filter(
                platform_id=self.instance.platform_id,
                active=True,
            )
        self.fields['date_limit'].widget = forms.DateTimeInput(
            format='%Y-%m-%d %H:%M:%S',
            attrs={'type': 'datetime-local'}
        )

    class Meta:
        model = Count
        fields = [
            'platform',
            'plan',
            'link',
            'country',
            'email',
            'date_limit',
            'sale_price',
            'profile_sale_price',
            'wholesale_price',
        ]


class CountPlanForm(forms.Form):

    def __init__(self, platform_id, purpose=None, *args, **kwargs):

        super(CountPlanForm, self).__init__(*args, **kwargs)
        plans = Plan.objects.filter(platform_id=platform_id, active=True)
        platform = Platform.objects.filter(id=platform_id).first()
        if (
            purpose == "inventory"
            and platform
            and platform.name.strip().casefold() == "iptv ibo pro player"
        ):
            plans = plans.filter(num_profiles=4)
        if (
            purpose == "inventory"
            and platform
            and is_chatgpt_plus_platform(platform.name)
        ):
            plans = plans.filter(num_profiles=6)
        if len(plans) > 0:
            self.fields['plan'] = forms.ModelChoiceField(queryset=plans, help_text='Selecciones el plan',  label="Plan")
        else:
            self.fields['plan'] = None




class PlanForm(forms.ModelForm):

    def __init__(self, platform, *args, **kwargs):
        super(PlanForm, self).__init__(*args, **kwargs)
        self.fields['num_profiles'] = forms.IntegerField(label="Perfiles a vender", widget=forms.NumberInput(
            attrs={'min': 1, 'max': platform.num_profiles,  'placeholder': 'Digite el numero de perfiles a vender en este plan'}))
        self.fields['have_link'].initial = False

    class Meta:
        model = Plan
        fields = [
            'name',
            'num_profiles',
            'sale_price',
            'wholesale_price',
            'have_link',
            'active',
            'description',
        ]


class ChangeCountDataForm(forms.Form):

    pin = forms.CharField(required=False, label="Pin")
    password = forms.CharField(required=False, label="Contraseña")


class ChangeSaleDataForm(forms.Form):

    def __init__(self, id, *args, **kwargs):

        super(ChangeSaleDataForm, self).__init__(*args, **kwargs)
        sale = Sale.objects.filter(id=id).first()
        self.fields['date'] = forms.DateField(
            label="Fecha de inicio",
            initial=sale.date.date() if sale and sale.date else None,
            input_formats=['%Y-%m-%d'],
            widget=forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'placeholder': 'Fecha de inicio'},
            ),
        )
        self.fields['date_limit'] = forms.DateField(
            label="Fecha de vencimiento",
            initial=sale.date_limit.date() if sale and sale.date_limit else None,
            input_formats=['%Y-%m-%d'],
            widget=forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'placeholder': 'Fecha de vencimiento'},
            ),
        )
        self.is_ibo_player = bool(sale and sale.is_ibo_player)
        if self.is_ibo_player:
            self.fields['device_mac'] = forms.CharField(
                required=False,
                max_length=17,
                initial=sale.device_mac,
                label="MAC address o Device ID",
                help_text="Déjalo vacío mientras el dispositivo esté pendiente.",
            )
            self.fields['device_key'] = forms.CharField(
                required=False,
                max_length=50,
                initial=sale.device_key,
                label="Clave del dispositivo",
                help_text="Déjala vacía mientras el dispositivo esté pendiente.",
            )

    def clean(self):
        cleaned_data = super().clean()
        if not getattr(self, 'is_ibo_player', False):
            return cleaned_data

        raw_mac = (cleaned_data.get('device_mac') or '').strip()
        device_key = (cleaned_data.get('device_key') or '').strip()
        device_mac = normalize_ibo_device_identifier(raw_mac) or ''
        if raw_mac and not device_mac:
            self.add_error('device_mac', 'Ingresa una MAC address o Device ID válido.')
        if bool(device_mac) != bool(device_key):
            raise forms.ValidationError(
                'Ingresa la MAC y la clave juntas, o deja ambas pendientes.'
            )
        cleaned_data['device_mac'] = device_mac
        cleaned_data['device_key'] = device_key
        return cleaned_data




class ChangePaswordForm(forms.ModelForm):
    class Meta:
        model = Count
        fields = ["password"]

class ChangePaswordEmailForm(ChangePaswordForm):

    class Meta(ChangePaswordForm.Meta):
        fields = ['email_password']


class SearchCountForm(forms.ModelForm):
    class Meta:
        model = Count
        fields = ["email", "platform"]


class ChangeDatePaswordForm(forms.ModelForm):
    class Meta:
        model = Count
        fields = ["password", 'date_limit']



class ChangeDateLimitForm(forms.ModelForm):

    class Meta:
        model = Count
        fields = ["date_limit"]


class CreatePromotionForm(forms.ModelForm):

    class Meta:
        model = Promotion
        fields = ["name", "price", "date_init", "date_finish", "active", "image"]


class CreatePlatformForm(forms.ModelForm):

    logo = forms.FileField(
        required=False,
        label="Logo",
        help_text="Opcional. Formatos permitidos: JPG, JPEG, PNG, GIF o BMP.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"placeholder": "Ej. Netflix"})
        self.fields["num_profiles"].widget.attrs.update({"min": 1, "max": 100})

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        queryset = Platform.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("Ya existe una plataforma con este nombre.")
        return name

    def clean_num_profiles(self):
        num_profiles = self.cleaned_data["num_profiles"]
        if num_profiles < 1 or num_profiles > 100:
            raise forms.ValidationError("Indique entre 1 y 100 perfiles.")
        return num_profiles

    class Meta:
        model = Platform
        fields = ["name", "active", "logo", "num_profiles"]


class PlatformForm(forms.Form):

    platforms = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple())

    class Meta:
        fields = ["platforms"]


class WholesalePublicationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["partner"].queryset = WholesalePartner.objects.filter(
            active=True
        ).select_related("customer")
        self.fields["plan"].queryset = Plan.objects.filter(
            active=True,
            platform__active=True,
        ).select_related("platform").order_by("platform__name", "name")
        self.fields["partner"].empty_label = "Seleccione un mayorista"
        self.fields["plan"].empty_label = "Seleccione plataforma y plan"
        self.fields["partner"].label_from_instance = (
            lambda partner: f"{partner.username} — {partner.customer.name}"
        )
        self.fields["plan"].label_from_instance = (
            lambda plan: f"{plan.platform.name} — {plan.name}"
        )

        for name, field in self.fields.items():
            if name in ("active", "featured"):
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control wholesale-control"})

        self.fields["wholesale_price"].widget.attrs.update(
            {"min": "0.01", "step": "0.01", "placeholder": "0.00"}
        )
        self.fields["stock_limit"].widget.attrs.update(
            {"min": "0", "placeholder": "0 = disponibilidad completa"}
        )
        self.fields["catalog_title"].widget.attrs.update(
            {"placeholder": "Ej. Netflix cuenta completa"}
        )
        self.fields["catalog_description"].widget.attrs.update(
            {"placeholder": "Descripción breve para el mayorista"}
        )
        self.fields["catalog_image"].widget.attrs.update(
            {"accept": "image/png,image/jpeg,image/webp"}
        )
        self.fields["sort_order"].widget.attrs.update({"min": "0"})

    class Meta:
        model = WholesalePublication
        fields = [
            "partner",
            "plan",
            "wholesale_price",
            "stock_limit",
            "catalog_title",
            "catalog_description",
            "catalog_image",
            "featured",
            "sort_order",
            "active",
        ]


class WholesaleSlideForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "active":
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control wholesale-control"})
        self.fields["image"].widget.attrs.update(
            {"accept": "image/png,image/jpeg,image/webp"}
        )
        self.fields["sort_order"].widget.attrs.update({"min": "0"})
        for name in ("starts_at", "ends_at"):
            self.fields[name].widget = forms.DateTimeInput(
                attrs={"class": "form-control wholesale-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            )
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M"]

    class Meta:
        model = WholesaleSlide
        fields = [
            "title",
            "subtitle",
            "image",
            "button_text",
            "button_url",
            "sort_order",
            "starts_at",
            "ends_at",
            "active",
        ]

    def clean(self):
        cleaned = super().clean()
        starts_at = cleaned.get("starts_at")
        ends_at = cleaned.get("ends_at")
        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error("ends_at", "La fecha final debe ser posterior a la inicial.")
        return cleaned
