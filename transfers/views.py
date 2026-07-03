from django.shortcuts import render
from .forms import TransferForm, TransferProductFormSet, TransferProductForm
from .models import Transfer, TransferProduct
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from warehouse.models import Warehouse
from inventory.models import Product
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from users.models import Membership
from django.core.exceptions import ValidationError


def _lock_and_validate_stock(requested_by_sku, assigned_warehouse, main_warehouse, company_id):
    warehouse_ids = []
    if assigned_warehouse and assigned_warehouse.company_id == company_id:
        warehouse_ids.append(assigned_warehouse.id)
    if main_warehouse and main_warehouse.id not in warehouse_ids:
        warehouse_ids.append(main_warehouse.id)

    products = Product.objects.select_for_update().filter(
        sku__in=requested_by_sku,
        product_location_id__in=warehouse_ids,
        company_id=company_id,
    )
    available_by_sku = {}
    for product in products:
        available_by_sku[product.sku] = available_by_sku.get(product.sku, 0) + max(
            product.stock_quantity - product.reserved_quantity,
            0,
        )

    for sku, requested_qty in requested_by_sku.items():
        total_available = available_by_sku.get(sku, 0)
        if total_available < requested_qty:
            raise ValidationError(
                f'Not enough stock for SKU {sku}. '
                f'Available total (assigned + main): {total_available}, Requested: {requested_qty}'
            )


def _collect_requested_transfer_items(form, formset):
    requested_items = []

    product = form.cleaned_data.get('product')
    quantity = form.cleaned_data.get('quantity')
    if product and quantity:
        requested_items.append({'product': product, 'quantity': int(quantity)})

    for row in formset:
        if not row.cleaned_data or row.cleaned_data.get('DELETE', False):
            continue
        extra_product = row.cleaned_data.get('product')
        extra_quantity = row.cleaned_data.get('quantity')
        if extra_product and extra_quantity:
            requested_items.append({'product': extra_product, 'quantity': int(extra_quantity)})

    return requested_items


@login_required
def transfers_list(request):
    user_company = get_object_or_404(Membership, user=request.user).company
    form = TransferForm(company_id=user_company.id)
    formset = TransferProductFormSet(instance=Transfer(), form_kwargs={'company_id': user_company.id})

    context = {
        'page': 'transfers',
        'form': form,
        'formset': formset,
        'transfers': Transfer.objects.filter(company_id=user_company.id).order_by('-created_on'),
    }
    return render(request, 'transfers/transfers_list.html', context)



@login_required
@require_POST
def create_transfer(request):
    user_company = get_object_or_404(Membership, user=request.user).company
    form = TransferForm(request.POST, company_id=user_company.id)
    formset = TransferProductFormSet(
        request.POST,
        instance=Transfer(),
        form_kwargs={'company_id': user_company.id},
    )

    if not form.is_valid() or not formset.is_valid():
        messages.error(request, 'Invalid form data.')
        return redirect('transfers:transfers_list')

    source_warehouse = form.cleaned_data['source_warehouse']
    destination_warehouse = form.cleaned_data['destination_warehouse']
    requested_items = _collect_requested_transfer_items(form, formset)

    if not source_warehouse or not destination_warehouse or not requested_items:
        messages.error(request, 'Invalid transfer data.')
        return redirect('transfers:transfers_list')

    requested_by_sku = {}
    for item in requested_items:
        sku = item['product'].sku
        requested_by_sku[sku] = requested_by_sku.get(sku, 0) + item['quantity']

    try:
        with transaction.atomic():
            _lock_and_validate_stock(
                requested_by_sku=requested_by_sku,
                assigned_warehouse=source_warehouse,
                main_warehouse=None,
                company_id=user_company.id,
            )

            source_products = Product.objects.select_for_update().filter(
                product_location=source_warehouse,
                sku__in=requested_by_sku,
                company_id=user_company.id,
            )
            source_products_by_sku = {product.sku: product for product in source_products}

            destination_products = Product.objects.select_for_update().filter(
                product_location=destination_warehouse,
                sku__in=requested_by_sku,
                company_id=user_company.id,
            )
            destination_products_by_sku = {product.sku: product for product in destination_products}

            transfer = Transfer.objects.create(
                source_warehouse=source_warehouse,
                destination_warehouse=destination_warehouse,
                notes=form.cleaned_data.get('notes', ''),
                created_by=request.user,
                company=user_company,
            )

            for sku, quantity in requested_by_sku.items():
                source_product_stock = source_products_by_sku.get(sku)
                if not source_product_stock:
                    raise ValidationError(f'Product with SKU {sku} not found in source warehouse.')

                destination_product_stock = destination_products_by_sku.get(sku)
                if not destination_product_stock:
                    destination_product_stock = Product.objects.create(
                        product_location=destination_warehouse,
                        sku=source_product_stock.sku,
                        name=source_product_stock.name,
                        description=source_product_stock.description,
                        category=source_product_stock.category,
                        price=source_product_stock.price,
                        reserved_quantity=0,
                        stock_quantity=0,
                        created_by=request.user,
                        company=user_company,
                    )
                    destination_products_by_sku[sku] = destination_product_stock

                source_product_stock.stock_quantity -= quantity
                source_product_stock.save(update_fields=['stock_quantity'])

                destination_product_stock.stock_quantity += quantity
                destination_product_stock.save(update_fields=['stock_quantity'])

            for item in requested_items:
                source_product_stock = source_products_by_sku[item['product'].sku]
                TransferProduct.objects.create(
                    transfer=transfer,
                    product=source_product_stock,
                    quantity=item['quantity'],
                    company=user_company,
                )

    except ValidationError as error:
        message = error.messages[0] if hasattr(error, 'messages') and error.messages else str(error)
        messages.error(request, message)
        return redirect('transfers:transfers_list')

    messages.success(request, 'Transfer created successfully.')
    return redirect('transfers:transfers_list')
    

@login_required
@require_POST
def edit_transfer(request, transfer_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    pass


@login_required
@require_POST
def delete_transfer(request, transfer_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    pass


@login_required
def get_products_by_warehouse(request, warehouse_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    products = Product.objects.filter(product_location_id=warehouse_id, company_id=user_company.id).values('id', 'name', 'sku', 'stock_quantity')
    return JsonResponse(list(products), safe=False)