from django.shortcuts import render
from .models import Customer
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from users.models import Membership
import json

_SORT_FIELDS = {
    'name':       'first_name',
    'email':      'email',
    'city':       'city',
    'created_on': 'created_on',
    'code':       'customer_code',
}


@login_required
def customers_list(request):
    membership = get_object_or_404(Membership, user=request.user)
    user_company = membership.company

    customers = Customer.objects.filter(company_id=user_company.id)

    search_query = request.GET.get('search', '').strip()
    sort_by      = request.GET.get('sort', 'created_on')
    sort_dir     = request.GET.get('dir', 'desc')

    if search_query:
        customers = customers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)  |
            Q(email__icontains=search_query)       |
            Q(city__icontains=search_query)        |
            Q(customer_code__icontains=search_query)
        )

    sort_field = _SORT_FIELDS.get(sort_by, 'first_name')
    customers = customers.order_by(f'-{sort_field}' if sort_dir == 'desc' else sort_field)

    no_rows   = request.GET.get('rows', '25')
    paginator = Paginator(customers, no_rows)
    page_obj  = paginator.get_page(request.GET.get('page'))

    if request.method == 'POST':
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name',  '').strip()
        email        = request.POST.get('email',      '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address      = request.POST.get('address',   '').strip()
        city         = request.POST.get('city',       '').strip()
        state        = request.POST.get('state',      '').strip()
        zip_code     = request.POST.get('zip_code',   '').strip()
        country      = request.POST.get('country',    '').strip()

        errors = {}
        if not first_name:
            errors['first_name'] = 'First name is required.'
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif Customer.objects.filter(email=email).exists():
            errors['email'] = 'A customer with this email already exists.'

        if errors:
            return JsonResponse({'ok': False, 'errors': errors}, status=400)

        customer = Customer.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number or None,
            address=address or None,
            city=city or None,
            state=state or None,
            zip_code=zip_code or None,
            country=country or None,
            created_by=request.user,
            company=user_company,
        )
        return JsonResponse({'ok': True, 'message': f'Customer {customer.get_full_name()} created.'})

    context = {
        'page':         'customers',
        'page_obj':     page_obj,
        'customers':    customers,
        'search_query': search_query,
        'sort_by':      sort_by,
        'sort_dir':     sort_dir,
        'no_rows':      no_rows,
    }
    return render(request, 'customers/customers_list.html', context)


@require_POST
@login_required
def edit_customer(request, customer_id):
    membership   = get_object_or_404(Membership, user=request.user)
    user_company = membership.company
    customer     = get_object_or_404(Customer, id=customer_id, company_id=user_company.id)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)

    first_name = data.get('first_name', '').strip()
    last_name  = data.get('last_name',  '').strip()
    email      = data.get('email',      '').strip()

    errors = {}
    if not first_name:
        errors['first_name'] = 'First name is required.'
    if not last_name:
        errors['last_name'] = 'Last name is required.'
    if not email:
        errors['email'] = 'Email is required.'
    elif Customer.objects.filter(email=email).exclude(id=customer_id).exists():
        errors['email'] = 'A customer with this email already exists.'

    if errors:
        return JsonResponse({'ok': False, 'errors': errors}, status=400)

    customer.first_name   = first_name
    customer.last_name    = last_name
    customer.email        = email
    customer.phone_number = data.get('phone_number', '').strip() or None
    customer.address      = data.get('address',      '').strip() or None
    customer.city         = data.get('city',         '').strip() or None
    customer.state        = data.get('state',        '').strip() or None
    customer.zip_code     = data.get('zip_code',     '').strip() or None
    customer.country      = data.get('country',      '').strip() or None
    customer.save()

    return JsonResponse({'ok': True, 'message': f'Customer {customer.get_full_name()} updated.'})
