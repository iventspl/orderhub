from .models import Product
from .forms import AddProductForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import ExpressionWrapper, F, IntegerField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from users.models import Membership, UserProfile
from sales.models import SalesOrder, SalesOrderItem
from packing.models import PackingOrderItem
from warehouse.models import Warehouse

_SORT_FIELDS = {
    'sku':       'sku',
    'name':      'name',
    'category':  'category',
    'price':     'price',
    'reserved':  'reserved_quantity',
    'store':     'store_stock',
    'warehouse': 'warehouse_stock',
}

def _store_stock_subquery():
    # Correlated subquery: net available stock (stock - reserved) across all SHOP
    # locations for the same SKU+company as the outer row. Two separate .annotate()
    # calls are required because Django cannot reference a Sum alias (s, r) inside
    # an ExpressionWrapper in the same annotate. [:1] turns it into a scalar subquery.
    return Subquery(
        Product.objects.filter(
            sku=OuterRef('sku'),
            company_id=OuterRef('company_id'),
            product_location__warehouse_type='SHOP',
        ).values('sku', 'company_id').annotate(
            s=Sum('stock_quantity'),
            r=Sum('reserved_quantity'),
        ).annotate(
            net=ExpressionWrapper(F('s') - F('r'), output_field=IntegerField())
        ).values('net')[:1],
        output_field=IntegerField(),
    )

def _warehouse_stock_subquery():
    # Same as _store_stock_subquery but scoped to MAIN warehouse type.
    return Subquery(
        Product.objects.filter(
            sku=OuterRef('sku'),
            company_id=OuterRef('company_id'),
            product_location__warehouse_type='MAIN',
        ).values('sku', 'company_id').annotate(
            s=Sum('stock_quantity'),
            r=Sum('reserved_quantity'),
        ).annotate(
            net=ExpressionWrapper(F('s') - F('r'), output_field=IntegerField())
        ).values('net')[:1],
        output_field=IntegerField(),
    )

@login_required
def inventory_list(request):
    membership = get_object_or_404(Membership, user=request.user)
    user_company = membership.company
    profile = UserProfile.objects.select_related('assigned_warehouse').filter(user=request.user).first()
    assigned_warehouse = profile.assigned_warehouse if profile else None
    main_warehouse = Warehouse.objects.filter(
        company=user_company,
        warehouse_type=Warehouse.WarehouseType.MAIN,
    ).first()

    # Scope the list to warehouses the user can actually access: the company's
    # main warehouse is always visible; a store-staff member also sees their
    # assigned shop. Users with no assignment only see the main warehouse.
    visible_warehouses = {w for w in [main_warehouse, assigned_warehouse] if w is not None}
    products = Product.objects.filter(
        company_id=user_company.id,
        product_location__in=visible_warehouses,
    )

    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(
            Q(sku__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    products = products.annotate(
        store_stock=Coalesce(_store_stock_subquery(), Value(0), output_field=IntegerField()),
        warehouse_stock=Coalesce(_warehouse_stock_subquery(), Value(0), output_field=IntegerField()),
    )

    sort_by  = request.GET.get('sort', 'name')
    sort_dir = request.GET.get('dir',  'asc')
    sort_field = _SORT_FIELDS.get(sort_by, 'name')
    products = products.order_by(f'-{sort_field}' if sort_dir == 'desc' else sort_field)

    no_rows   = request.GET.get('rows', '25')
    paginator = Paginator(products, no_rows)
    page_obj  = paginator.get_page(request.GET.get('page'))

    _privileged = {Membership.Roles.ADMIN, Membership.Roles.MANAGER}
    context = {
        'page':         'inventory',
        'form':         AddProductForm(company_id=user_company.id),
        'products':     products,
        'page_obj':     page_obj,
        'no_rows':      no_rows,
        'search_query': search_query,
        'sort_by':      sort_by,
        'sort_dir':     sort_dir,
        'can_edit':     membership.role in _privileged,
    }
    return render(request, 'inventory/inventory_list.html', context)



@login_required
@require_POST
def add_product(request):
    user_company = get_object_or_404(Membership, user=request.user).company
    form = AddProductForm(request.POST, request.FILES, company_id=user_company.id)

    if form.is_valid():
        cleaned = form.cleaned_data
        profile = UserProfile.objects.select_related('assigned_warehouse').filter(user=request.user).first()
        default_location = profile.assigned_warehouse if profile else None
        # Form location is optional; fall back to the user's assigned warehouse so
        # store staff don't have to pick it explicitly on every new product.
        product_location = cleaned['product_location'] or default_location

        if not product_location:
            messages.error(request, 'No warehouse selected and no assigned warehouse found for your profile.')
            return redirect('inventory:inventory_list')

        product = Product.objects.create(
            sku=cleaned['product_sku'],
            name=cleaned['product_name'],
            category=cleaned['product_category'],
            description=cleaned.get('product_description'),
            stock_quantity=cleaned['stock_quantity'],
            price=cleaned['price'],
            product_location=product_location,
            bin_location=cleaned.get('bin_location'),
            created_by=request.user,
            company = user_company,
            product_image=cleaned.get('product_image')
        )
        messages.success(request, f'Added {product.stock_quantity} of {product.name} to inventory.')
    else:
        messages.error(request, 'Failed to add Product. Please correct the errors below.')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect('inventory:inventory_list')



@login_required
@require_POST
def edit_product(request, product_id):
    # Called via fetch() from the JS edit modal, so responds with JSON rather than a redirect.
    user_company = get_object_or_404(Membership, user=request.user).company
    product = get_object_or_404(Product, id=product_id, company_id=user_company.id)

    form = AddProductForm(request.POST, request.FILES, company_id=user_company.id, product_instance=product)
    if form.is_valid():
        cleaned = form.cleaned_data
        product.sku = cleaned['product_sku']
        product.name = cleaned['product_name']
        product.category = cleaned['product_category']
        product.description = cleaned.get('product_description')
        product.stock_quantity = cleaned['stock_quantity']
        product.price = cleaned['price']
        product.product_location = cleaned['product_location']
        product.bin_location = cleaned.get('bin_location')
        if cleaned.get('remove_image'):
            product.product_image = None
        elif cleaned.get('product_image'):
            product.product_image = cleaned.get('product_image')
        product.save()
        return JsonResponse({
            'success': True,
            'message': f'Updated {product.name} in inventory.'
        })
    else:
        errors = {field: error[0] if error else '' for field, error in form.errors.items()}
        return JsonResponse({
            'success': False,
            'message': 'Validation failed.',
            'errors': errors
        }, status=400)


ACTIVE_ORDER_STATUSES = {
    SalesOrder.SalesOrderStatus.DRAFT,
    SalesOrder.SalesOrderStatus.IN_WAREHOUSE,
    SalesOrder.SalesOrderStatus.PACKED,
}

@login_required
@require_POST
def delete_product(request, product_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    product = get_object_or_404(Product, id=product_id, company_id=user_company.id)
    product_name = product.name

    # Block deletion if any order using this product is still active.
    blocking_order = SalesOrderItem.objects.filter(
        product=product,
        order__status__in=ACTIVE_ORDER_STATUSES,
    ).select_related('order').first()

    if blocking_order:
        messages.error(
            request,
            f'Cannot delete "{product_name}": order {blocking_order.order.order_number} '
            f'is still {blocking_order.order.get_status_display()}. '
            f'Finish or cancel all active orders before deleting this product.'
        )
        return redirect('inventory:inventory_list')

    # Block deletion if stock is still reserved for a pending shipment.
    if product.reserved_quantity > 0:
        messages.error(
            request,
            f'Cannot delete "{product_name}": {product.reserved_quantity} unit(s) are still reserved. '
            f'All reservations must be cleared before deleting this product.'
        )
        return redirect('inventory:inventory_list')

    with transaction.atomic():
        # Back-fill snapshot fields that were never populated before the FK goes NULL.
        # Each field is updated independently to avoid overwriting a valid historical value.
        SalesOrderItem.objects.filter(product=product, product_sku='').update(product_sku=product.sku)
        SalesOrderItem.objects.filter(product=product, product_name='').update(product_name=product.name)
        PackingOrderItem.objects.filter(product=product, product_sku='').update(product_sku=product.sku)
        PackingOrderItem.objects.filter(product=product, product_name='').update(product_name=product.name)
        # product.delete() sets SalesOrderItem.product and PackingOrderItem.product to NULL
        # via SET_NULL — all order records are preserved with their name/sku snapshots.
        product.delete()

    messages.success(request, f'Deleted {product_name} from inventory.')
    return redirect('inventory:inventory_list')