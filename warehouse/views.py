import json

from .forms import WarehouseForm
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from users.models import Membership
from inventory.models import Product
from sales.models import SalesOrderItem
from .models import Warehouse



def _warehouse_payload(warehouse):
    products = [
        {
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'reserved_quantity': product.reserved_quantity,
            'stock_quantity': product.stock_quantity,
        }
        for product in warehouse.get_warehouse_products().order_by('name', 'sku')
    ]
    return {
        'id': warehouse.id,
        'name': warehouse.name,
        'address': warehouse.address,
        'city': warehouse.city,
        'zip_code': warehouse.zip_code,
        'country': warehouse.country,
        'notes': warehouse.notes or '',
        'capacity_usage': warehouse.capacity_usage(),
        'active_zones': warehouse.active_zones(),
        'products': products,
    }


@login_required
def warehouse_list(request, warehouse_type=None):
    user_company = get_object_or_404(Membership, user=request.user)
    warehouses = Warehouse.objects.filter(company_id=user_company.company_id).order_by('-created_on')
    if warehouse_type:
        warehouse_type = warehouse_type.upper()
        warehouses = warehouses.filter(warehouse_type=warehouse_type)
    warehouses_map = {str(warehouse.id): _warehouse_payload(warehouse) for warehouse in warehouses}
    form = WarehouseForm()
    context = {
        'page': 'warehouse',
        'warehouses': warehouses,
        'warehouses_map_json': json.dumps(warehouses_map),
        'form': form,
    }
    return render(request, 'warehouse/warehouse_list.html', context)


@require_POST
@login_required
def get_warehouse_types(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        error_msg = 'Invalid JSON payload.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg}, status=400)
    
    warehouse_type = data.get('warehouse_type')
    if warehouse_type:
        warehouse_type = warehouse_type.upper()

    if warehouse_type == 'ALL':
        return redirect('warehouse:warehouse_list')

    if warehouse_type not in dict(Warehouse.WarehouseType.choices):
        error_msg = 'Invalid warehouse type.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg}, status=400)

    return redirect('warehouse:warehouse_list_by_type', warehouse_type=warehouse_type)


@require_POST
@login_required
def create_warehouse(request):
    form = WarehouseForm(request.POST)

    if form.is_valid():
        warehouse = form.save(commit=False)
        warehouse.created_by = request.user
        warehouse.company = get_object_or_404(Membership, user=request.user).company
        warehouse.save()
        messages.success(request, f'Warehouse {warehouse.name} created successfully.')
        return redirect('warehouse:warehouse_list')
    else:
        error_msg = 'Invalid form data.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg}, status=400)



@require_POST
@login_required
def edit_warehouse(request, warehouse_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    warehouse = get_object_or_404(Warehouse, pk=warehouse_id, company=user_company)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        error_msg = 'Invalid JSON payload.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg}, status=400)

    notes = data.get('notes')
    products_data = data.get('products', [])
    if not isinstance(products_data, list):
        error_msg = 'products must be a list.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg}, status=400)

    with transaction.atomic():
        if notes is not None:
            warehouse.notes = str(notes).strip()
            warehouse.save(update_fields=['notes'])

        for row in products_data:
            if not isinstance(row, dict):
                continue

            product_id = row.get('id')
            stock_quantity = row.get('stock_quantity')
            if product_id is None or stock_quantity is None:
                continue

            try:
                stock_quantity = int(stock_quantity)
            except (TypeError, ValueError):
                error_msg = f'Invalid stock quantity for product id {product_id}.'
                messages.error(request, error_msg)
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)

            if stock_quantity < 0:
                error_msg = f'Stock quantity cannot be negative (product id {product_id}).'
                messages.error(request, error_msg)
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)

            product = Product.objects.select_for_update().filter(pk=product_id, product_location=warehouse).first()
            if not product:
                error_msg = f'Product id {product_id} not found in this warehouse.'
                messages.error(request, error_msg)
                return JsonResponse({'ok': False, 'error': error_msg}, status=404)

            if stock_quantity < product.reserved_quantity:
                error_msg = (
                    f'Cannot set stock below reserved quantity for SKU {product.sku}. '
                    f'Reserved: {product.reserved_quantity}.'
                )
                messages.error(request, error_msg)
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)

            product.stock_quantity = stock_quantity
            product.save(update_fields=['stock_quantity'])

    success_msg = f'Warehouse {warehouse.name} updated successfully.'
    messages.success(request, success_msg)
    return JsonResponse({'ok': True, 'message': success_msg, 'warehouse': _warehouse_payload(warehouse)})


@require_POST
@login_required
def delete_warehouse_product(request, warehouse_id, product_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    warehouse = get_object_or_404(Warehouse, pk=warehouse_id, company_id=user_company.id)
    product = get_object_or_404(Product, pk=product_id, product_location=warehouse, company_id=user_company.id)

    if product.reserved_quantity > 0:
        error_msg = f'Cannot delete SKU {product.sku}. Reserved quantity must be 0 first.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg}, status=400)

    TERMINAL_STATUSES = {'DELIVERED', 'PAID'}

    active_sales = SalesOrderItem.objects.filter(product=product, order__company_id=user_company.id).exclude(
        order__status__in=TERMINAL_STATUSES
    )
    if active_sales.exists():
        statuses = list(active_sales.values_list('order__status', flat=True).distinct())
        error_msg = (
            f'Cannot delete SKU {product.sku}. Active orders still reference this product '
            f'(statuses: {", ".join(statuses)}).'
        )
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg}, status=400)

    with transaction.atomic():
        # Sales/Packing items keep snapshot fields; only FK is set to NULL.
        product.delete()

    success_msg = f'Product {product.sku} removed from warehouse {warehouse.name}.'
    messages.success(request, success_msg)
    return JsonResponse({'ok': True, 'message': success_msg, 'product_id': product_id})
