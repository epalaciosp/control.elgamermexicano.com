from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from django.urls import resolve
from functools import wraps

def check_user_type(request):    
    if request.user.is_superuser:
        return "superuser"

    group = Group.objects.filter(user=request.user).order_by("id").first()
    return group.name if group else "sin_rol"



def usertype_in_view(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        staff = ['saler-add',
                 'saler-list',
                 'delete-table-id',
                 'platforms-list',
                 'add-subproduct',
                 'edit-package',
                 'add-count-package',
                 'multiplatforms-sales',
                 'reported-issue',
                 'send-package-to-markeplace',
                 'market-place',
                 'my-packages-in-market-place',
                 'multiplatforms-sales-month',
                 'sales-inter-dates',
                 'general-sales',
                 'commission-collect',
                 'commission-payed',
                 'renew-count-package-list',
                 'renew-count-package',
                 'see-sale',
                 'deny-renew-count-package'
                 ]
        vendedor = ['platforms',
                    'sale-count-package',
                    'buy-platform',
                    'multiplatforms-sales',
                    'report-issue-platform',
                    'delete-table-id',
                    'market-place',
                    'qualify-saler-list',
                    'qualify-saler',
                    'multiplatforms-sales-month',
                    'general-sales',
                    'buys-inter-dates',
                    'resale-count-package'
                    ]
        superuser = ['add-product',
                     'staff-list',
                     'activate-staff',
                     'check-username',
                     'activate-ajax-staff',
                     'delete-table-id',
                     'reported-issue',
                     'add-money-saler',
                     'money-saler-list',
                     'market-place',
                     'multiplatforms-sales',
                     'commision-pending',
                     'pay-staff-sale',
                     'multiplatforms-sales-month',
                     'sales-inter-dates',
                     'user-pay-pending',
                     'see-sale',
                     'pay-invoice-pendding'
                     ]
        allowed_by_role = {
            "staff": staff,
            "vendedor": vendedor,
            "superuser": superuser,
        }
        request_url = request.path_info
        match = resolve(request_url)
        url_name = match.url_name
        user_type = check_user_type(request)
        if url_name in allowed_by_role.get(user_type, []):
            return function(request, *args, **kwargs)        
        raise PermissionDenied

    return wrap

