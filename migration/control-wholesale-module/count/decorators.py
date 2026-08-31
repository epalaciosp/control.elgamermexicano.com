from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.urls import resolve

PERMISSION_BY_VIEW = {
    'create-platform' : ['add_platform'],
    'update-platform' : ['change_platform'],
    'toggle-platform-status' : ['change_platform'],
    'delete-platform' : ['delete_platform'],
    'set-prices_by-profiles' : ['add_platform', 'change_platform'],
    'add-customer' : ['add_customer'],
    'update-customer' : ['change_customer'],
    'add-user' : ['add_user'],
    'create-count': ['add_count'],
    'edit-count-data': ['change_count'],
    'delete-count': ['delete_count'],
    'change-date-limit': ['change_count'],
    'create-promotion': ['add_promotion'],
    'sale-count': ['add_sale'],
    'edit-sale-data':  ['change_count'],
    'create-pins-profiles':  ['add_count'],
    'cut-profile': ['change_count'],
    'owner-profile': ['change_count'],
    'create-plan': ['add_plan'],
    'update-plan': ['change_plan'],
    'update-count': ['change_count'],
    'list-user': ['view_user', 'add_user', 'change_user'],
    'update-user': ['change_user'],
    'toggle-user-status': ['change_user'],
}

SUPERUSER_ONLY_VIEWS = {'add-user', 'update-user', 'toggle-user-status'}

def my_permissions(user):
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        return {'*'}
    return {permission.split('.', 1)[-1] for permission in user.get_all_permissions()}


def permissions_in_view(function):

    def wrap(request, *args, **kwargs):

        permissions = my_permissions(request.user)
        request_url = request.__dict__['path_info'] #captura todo el request en un dict
        match = resolve(request_url) #devuelve el name de la vista
        url_name = match.url_name
        required_permissions = PERMISSION_BY_VIEW.get(url_name)
        if required_permissions is None:
            raise PermissionDenied
        if url_name in SUPERUSER_ONLY_VIEWS and '*' not in permissions:
            raise PermissionDenied
        if '*' in permissions or permissions.intersection(required_permissions):
            return function(request, *args, **kwargs)
        raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
