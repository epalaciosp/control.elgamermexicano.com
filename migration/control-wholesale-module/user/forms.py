from django import forms
from .models import Customer
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User, Permission


PROTECTED_SUPERUSER_USERNAMES = frozenset({'epalacios10', 'epalaciosp'})

PERMISSIONS_ACTIVES = [
    'view_platform',
    'add_platform',
    'change_platform',
    'delete_platform',
    'add_customer',
    'change_customer',
    'delete_customer',
    'view_user',
    'add_count',
    'change_count',
    'delete_count',
    'add_promotion',
    'delete_sale',
    'add_sale',
    'add_plan',
    'change_plan',
    'manage_myplataforma',
]

PERMISSION_LABELS = {
    'view_platform': 'Ver plataformas',
    'add_platform': 'Crear plataformas',
    'change_platform': 'Editar plataformas',
    'delete_platform': 'Eliminar plataformas sin uso',
    'add_customer': 'Crear clientes',
    'change_customer': 'Editar clientes',
    'delete_customer': 'Eliminar clientes',
    'view_user': 'Ver colaboradores',
    'add_count': 'Crear cuentas',
    'change_count': 'Editar cuentas y servicios',
    'delete_count': 'Eliminar cuentas',
    'add_promotion': 'Crear promociones',
    'delete_sale': 'Cortar servicios',
    'add_sale': 'Registrar ventas',
    'add_plan': 'Crear planes',
    'change_plan': 'Editar planes',
    'manage_myplataforma': 'Administrar MyPlataforma',
}


class BusinessPermissionChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, permission):
        return PERMISSION_LABELS.get(permission.codename, permission.name)


def active_permissions_queryset():
    return Permission.objects.filter(codename__in=PERMISSIONS_ACTIVES).order_by(
        'content_type__app_label', 'codename'
    )


class UserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_permissions = BusinessPermissionChoiceField(
        queryset=active_permissions_queryset(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Permisos del colaborador',
    )

    class Meta:
        model = User
        fields = [
            'username', 'password1', 'password2', 'first_name', 'last_name',
            'email', 'is_active', 'is_staff', 'user_permissions',
        ]


class CollaboratorUpdateForm(forms.ModelForm):
    user_permissions = BusinessPermissionChoiceField(
        queryset=active_permissions_queryset(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Permisos del colaborador',
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'is_active', 'is_staff', 'user_permissions',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_protected_account = (
            self.instance
            and self.instance.username.casefold() in PROTECTED_SUPERUSER_USERNAMES
        )
        if self.is_protected_account:
            for field_name in ('username', 'is_active', 'is_staff', 'user_permissions'):
                self.fields[field_name].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        if self.is_protected_account:
            cleaned_data['username'] = self.instance.username
            cleaned_data['is_active'] = True
            cleaned_data['is_staff'] = True
        return cleaned_data


class CustomerForm(forms.ModelForm):
    name = forms.CharField(max_length=140, required=True)
    phone = forms.CharField(required=True)

    class Meta:
        model = Customer
        fields = ['name', 'phone']


class CustomUserChangeForm(UserChangeForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=active_permissions_queryset(),
        widget=forms.SelectMultiple,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_login', 'user_permissions',
            'last_name', 'email', 'password1', 'password2', 'is_active', 'is_staff',
        ]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomUserCreationForm(UserCreationForm):
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=active_permissions_queryset(),
        widget=forms.SelectMultiple,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'username', 'last_login', 'first_name', 'user_permissions',
            'last_name', 'email', 'password1', 'password2', 'is_active', 'is_staff',
        ]
