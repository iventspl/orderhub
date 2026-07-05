from django.shortcuts import render, redirect
from django.contrib import messages
import json
from mainapp.models import Logger
from .models import SalesOrder, SalesOrderItem
from customers.models import Customer
from inventory.models import Product
from warehouse.models import Warehouse
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from users.models import UserProfile, Membership, Company
from tracking.models import Tracking
from packing.models import PackingOrder, PackingOrderItem
from .forms import SalesOrderForm, SalesOrderItemFormSet
from django.shortcuts import get_object_or_404


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
        


@login_required
def sales_list(request, no_rows=10):
    membership = get_object_or_404(Membership, user=request.user)
    user_company = membership.company
    if not user_company:
        messages.error(request, 'User does not belong to any company.')
        return redirect('home')
    """View to display the list of sales orders and handle creation of new orders."""
    sales_orders = SalesOrder.objects.filter(company_id=user_company.id).order_by('-created_on')
    status_filters = SalesOrder.SalesOrderStatus.choices

    # filtering options
    status_filter = request.GET.get('filter_status', '').upper()
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort_by')
    sort_dir = request.GET.get('sort_dir')

    if status_filter and status_filter != 'ALL':
        sales_orders = sales_orders.filter(status=status_filter)
    if search_query:
        sales_orders = sales_orders.filter(
            customer__first_name__icontains=search_query
        ) | sales_orders.filter(
            customer__last_name__icontains=search_query
        ) | sales_orders.filter(
            order_number__icontains=search_query
        ) | sales_orders.filter(
            customer__city__icontains=search_query
        )
    if sort_by in ['created_on', 'order_number', 'customer', 'value', 'status'] and sort_dir in ['asc', 'desc']:
        sort_by = f'-{sort_by}' if sort_dir == 'desc' else sort_by
        sales_orders = sales_orders.order_by(sort_by)

    # number of rows for pagination
    no_rows = request.GET.get('rows')
    if no_rows:
        paginator = Paginator(sales_orders, no_rows)
    else:
        no_rows = 10
        paginator = Paginator(sales_orders, no_rows)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        form = SalesOrderForm(request.POST, company_id=user_company.id)
        formset = SalesOrderItemFormSet(request.POST, form_kwargs={'company_id': user_company.id})
        is_new_customer = request.POST.get('is_new_customer')
        # Pole renderuje się jako name="ship_to". Domyślnie traktujemy brak wartości jako STORE.
        ship_to_value = request.POST.get('ship_to') or SalesOrder.SalesShipTo.STORE
        ship_to_customer = ship_to_value == SalesOrder.SalesShipTo.CUSTOMER

        
        # Process form data and create a new SalesOrder if the form is valid
        if form.is_valid() and formset.is_valid():
            if is_new_customer:
                # Implement logic to create a new customer and associate it with the order
                customer_first_name = request.POST.get('customer_first_name')
                customer_last_name = request.POST.get('customer_last_name')
                customer_email = request.POST.get('customer_email')
                customer_phone_number = request.POST.get('customer_phone')
                customer_address = request.POST.get('customer_address')
                customer_city = request.POST.get('customer_city')
                customer_state = request.POST.get('customer_state')
                customer_zip_code = request.POST.get('customer_zip_code')
                customer_country = request.POST.get('customer_country')
                customer = Customer.objects.create(
                    first_name=customer_first_name,
                    last_name=customer_last_name,
                    email=customer_email,
                    phone_number=customer_phone_number,
                    address=customer_address,
                    city=customer_city,
                    state=customer_state,
                    zip_code=customer_zip_code,
                    country=customer_country,
                    created_by=request.user,
                    company=user_company
                )
            
            requested_by_sku = {}
            for row in formset.cleaned_data:
                product = row.get('product')
                quantity = row.get('quantity')
                should_delete = row.get('DELETE', False)
                if should_delete or not product or not quantity:
                    continue
                requested_by_sku[product.sku] = requested_by_sku.get(product.sku, 0) + int(quantity)

            if not requested_by_sku:
                messages.error(request, 'At least one product must be added to the order.')
                return redirect('sales:sales_list')

            assigned_warehouse = None
            profile = UserProfile.objects.select_related('assigned_warehouse').filter(user=request.user).first()
            if profile:
                assigned_warehouse = profile.assigned_warehouse

            main_warehouse = Warehouse.objects.filter(
                warehouse_type=Warehouse.WarehouseType.MAIN,
                company_id=user_company.id,
            ).first()

            
            order = form.save(commit=False)
            order.created_by = request.user
            order.customer = customer if is_new_customer else form.cleaned_data['customer']
            order.company = user_company
            if not order.customer:
                messages.error(request, 'Customer is required.')
                return redirect('sales:sales_list')
            if ship_to_customer:
                ship_customer_first_name = request.POST.get('ship_to_customer_first_name')
                ship_customer_last_name = request.POST.get('ship_to_customer_last_name')
                ship_customer_email = request.POST.get('ship_to_customer_email')
                ship_customer_phone_number = request.POST.get('ship_to_customer_phone')
                ship_customer_address = request.POST.get('ship_to_customer_address')
                ship_customer_city = request.POST.get('ship_to_customer_city')
                ship_customer_state = request.POST.get('ship_to_customer_state')
                ship_customer_zip_code = request.POST.get('ship_to_customer_zip_code')
                ship_customer_country = request.POST.get('ship_to_customer_country')
                order.ship_address = f"CUSTOMER: {ship_customer_first_name.title().strip()} {ship_customer_last_name.title().strip()}, \n email: {ship_customer_email.strip()}, \n tel: {ship_customer_phone_number.strip()}, \n {ship_customer_address.strip()}, {ship_customer_zip_code.strip()},  {ship_customer_city.title().strip()}, \n {ship_customer_state.title().strip()}, {ship_customer_country.title().strip()}"
            try:
                with transaction.atomic():
                    _lock_and_validate_stock(
                        requested_by_sku,
                        assigned_warehouse,
                        main_warehouse,
                        user_company.id,
                    )
                    if not ship_to_customer:
                        order.ship_address = f"COMPANY: {user_company.address}, {user_company.zip_code}, {user_company.city}, {user_company.state}, {user_company.country}"
                    order.save()
                    Tracking.objects.create(order=order, company_id=user_company.id, tracking_number='Waiting for packing', carrier=Tracking.TrackingCarrier.OTHER, status=Tracking.TrackingStatus.PENDING)
                    formset.instance = order
                    for item_form in formset.forms:
                        if item_form.instance.pk is None:
                            item_form.instance.company_id = user_company.id
                    formset.save()
                    order.calculate_value()
            except ValidationError as error:
                messages.error(request, error.messages[0])
                return redirect('sales:sales_list')
            items = order.salesorderitem_set.all()
            items_str = ', '.join(f'{i.resolved_name} x{i.quantity}' for i in items)
            Logger.objects.create(
                action=f"Order {order.order_number} created",
                user=request.user,
                details=f"Order {order.order_number} created for {order.customer} | Items: {items_str}",
                content_object=order
            )
            messages.success(request, f'Order {order.order_number} created for {order.customer} | Items: {items_str}')

            
            return redirect('sales:sales_list')
    else:
        form = SalesOrderForm(company_id=user_company.id)
        formset = SalesOrderItemFormSet(form_kwargs={'company_id': user_company.id})

    order_items_map = {
        str(order.id): [
            {
                'sku': item.resolved_sku,
                'name': item.resolved_name,
                'quantity': item.quantity,
            }
            for item in order.salesorderitem_set.select_related('product').all()
        ]
        for order in page_obj.object_list
    }

    context = {
        'page': 'sales',
        "page_obj": page_obj,
        'sales_orders': sales_orders,
        'no_rows': no_rows,
        'form' : form,
        'formset' :formset,
        'order_items_map_json': json.dumps(order_items_map),
        'status_filter': status_filter or 'ALL',
        'search_query': search_query or '',
        'sort_by': request.GET.get('sort_by') or '',
        'sort_dir': sort_dir or '',
        'status_filters': status_filters,
        'can_edit': membership.role in {Membership.Roles.ADMIN, Membership.Roles.MANAGER},
    }
    return render(request, 'sales/sales_list.html', context)


@require_POST
@login_required
def edit_sales_order(request):
    user_company = get_object_or_404(Membership, user=request.user).company

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        error_msg = 'Invalid JSON payload.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)

    order_id = data.get('order_id')
    if not order_id:
        error_msg = 'order_id is required.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)

    order = SalesOrder.objects.filter(id=order_id).first()
    if not order:
        error_msg = 'Order not found.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=404)

    if order.status not in ['DRAFT', 'IN WAREHOUSE', 'PACKED', 'SHIPPED']:
        error_msg = 'Only orders in DRAFT, IN WAREHOUSE, PACKED, or SHIPPED status can be edited.'
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)

    try:
        editable_statuses = {choice for choice, _ in SalesOrder.SalesOrderStatus.choices}
        new_status = data.get('new_status')
        items_data = data.get('items', [])

        warnings = []

        with transaction.atomic():
            if new_status and new_status != order.status:
                if new_status not in editable_statuses:
                    error_msg = 'Invalid status value.'
                    messages.error(request, error_msg)
                    return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)
                order.status = new_status
                order.save(update_fields=['status'])
                Logger.objects.create(
                    action=f"Order {order.order_number} status changed to {new_status}",
                    user=request.user,
                    details=f"User {request.user.profile.get_full_name()} ({request.user.profile.email}) changed order {order.order_number} status to {new_status}",
                    content_object=order
                )
                # signals będą reagować na zmianę statusu i odpowiednio rezerwować/zwalniać produkty, tworzyć pozycje pakowania itp.

            if not isinstance(items_data, list):
                error_msg = 'items must be a list.'
                messages.error(request, error_msg)
                return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)

            assigned_warehouse = None
            if order.created_by_id:
                profile = UserProfile.objects.select_related('assigned_warehouse').filter(user=order.created_by).first()
                if profile:
                    assigned_warehouse = profile.assigned_warehouse

            main_warehouse = Warehouse.objects.filter(warehouse_type=Warehouse.WarehouseType.MAIN, company_id=user_company.id).first()

            order_items = SalesOrderItem.objects.select_related('product').filter(order=order, company_id=user_company.id)
            order_items_by_sku = {item.resolved_sku: item for item in order_items if item.resolved_sku}

            packing_order = PackingOrder.objects.filter(order=order, company_id=user_company.id).first()
            stock_already_deducted = bool(packing_order and packing_order.stock_deducted)

            for item_data in items_data:
                if not isinstance(item_data, dict):
                    continue

                sku = item_data.get('sku')
                quantity = item_data.get('quantity')
                if sku is None or quantity is None:
                    continue

                item = order_items_by_sku.get(sku)
                if not item:
                    continue

                try:
                    quantity = int(quantity)
                except (TypeError, ValueError):
                    error_msg = f'Invalid quantity for SKU {sku}.'
                    messages.error(request, error_msg)
                    return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)

                if quantity < 1:
                    error_msg = f'Quantity for SKU {sku} must be at least 1.'
                    messages.error(request, error_msg)
                    return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)

                # Status-only edits (e.g. SHIPPED -> DELIVERED) must not recalculate reservations,
                # otherwise we can create phantom reservations in MAIN warehouse.
                if quantity == item.quantity:
                    continue

                if stock_already_deducted:
                    error_msg = (
                        f'Cannot change quantity for SKU {sku} because stock has already been deducted '
                        'during packing/shipping flow.'
                    )
                    messages.error(request, error_msg)
                    return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)

                # Release previous reservation amounts tracked on the order item.
                if item.reserved_from_assigned and assigned_warehouse:
                    assigned_product = Product.objects.select_for_update().filter(
                        sku=item.resolved_sku,
                        product_location=assigned_warehouse,
                        company_id=user_company.id
                    ).first()
                    if assigned_product:
                        assigned_product.reserved_quantity = max(
                            assigned_product.reserved_quantity - item.reserved_from_assigned,
                            0,
                        )
                        assigned_product.save(update_fields=['reserved_quantity'])

                if item.reserved_from_main and main_warehouse:
                    main_product_for_release = Product.objects.select_for_update().filter(
                        sku=item.resolved_sku,
                        product_location=main_warehouse,
                        company_id=user_company.id
                    ).first()
                    if main_product_for_release:
                        main_product_for_release.reserved_quantity = max(
                            main_product_for_release.reserved_quantity - item.reserved_from_main,
                            0,
                        )
                        main_product_for_release.save(update_fields=['reserved_quantity'])

                remaining_qty = quantity
                new_reserved_assigned = 0
                new_reserved_main = 0

                # Reserve from assigned warehouse first.
                if assigned_warehouse:
                    assigned_product = Product.objects.select_for_update().filter(
                        sku=item.resolved_sku,
                        product_location=assigned_warehouse,
                        company_id=user_company.id
                    ).first()
                    if assigned_product:
                        print(
    "ASSIGNED PRODUCT",
    assigned_product.id if assigned_product else None,
    assigned_product.product_location_id if assigned_product else None,
)
                        available_assigned = max(assigned_product.stock_quantity - assigned_product.reserved_quantity, 0)
                        new_reserved_assigned = min(available_assigned, remaining_qty)
                        if new_reserved_assigned:
                            assigned_product.reserved_quantity += new_reserved_assigned
                            assigned_product.save(update_fields=['reserved_quantity'])
                            remaining_qty -= new_reserved_assigned

                # Reserve missing part from MAIN warehouse.
                if remaining_qty > 0 and main_warehouse:
                    main_product = Product.objects.select_for_update().filter(
                        sku=item.resolved_sku,
                        product_location=main_warehouse,
                        company_id=user_company.id
                    ).first()
                    if main_product:
                        available_main = max(main_product.stock_quantity - main_product.reserved_quantity, 0)
                        new_reserved_main = min(available_main, remaining_qty)
                        if new_reserved_main:
                            main_product.reserved_quantity += new_reserved_main
                            main_product.save(update_fields=['reserved_quantity'])
                            remaining_qty -= new_reserved_main

                if remaining_qty > 0:
                    warnings.append(f'Not enough stock to fully reserve SKU {sku}. Missing quantity: {remaining_qty}.')

                item.quantity = quantity
                item.reserved_from_assigned = new_reserved_assigned
                item.reserved_from_main = new_reserved_main
                item.save(update_fields=['quantity', 'reserved_from_assigned', 'reserved_from_main'])
                Logger.objects.create(
                    action=f"Order {order.order_number} item updated for SKU {sku}",
                    user=request.user,
                    details=f"User {request.user.profile.get_full_name()} ({request.user.profile.email}) updated order {order.order_number} item for SKU {sku}. New quantity: {quantity}, Reserved from assigned: {new_reserved_assigned}, Reserved from main: {new_reserved_main}",
                    content_object=order
                )

            # Synchronizacja PackingOrder dopiero po przeliczeniu wszystkich pozycji.
            # Dzięki temu nie usuwamy zamówienia pakowania "za wcześnie" przy edycji jednej linii.
            # Pomijamy sync dla DELIVERED/CANCELLED – sygnał post_save już obsługuje czyszczenie.
            terminal_status = new_status in (
                SalesOrder.SalesOrderStatus.DELIVERED,
                SalesOrder.SalesOrderStatus.CANCELLED,
            )
            if not stock_already_deducted and not terminal_status:
                refreshed_items = list(
                    SalesOrderItem.objects.select_for_update().filter(order=order, company_id=user_company.id)
                )
                items_requiring_main = [row for row in refreshed_items if row.reserved_from_main > 0]

                if items_requiring_main and not packing_order:
                    packing_order = PackingOrder.objects.create(
                        order=order,
                        status=PackingOrder.PackingStatus.PENDING,
                        company_id=user_company.id
                    )
                print("=== REFRESHED ITEMS ===")
                for row in refreshed_items:
                    print(
                        f"item={row.id}",
                        f"sku={row.resolved_sku}",
                        f"qty={row.quantity}",
                        f"assigned={row.reserved_from_assigned}",
                        f"main={row.reserved_from_main}",
                    )
                if packing_order:
                    for row in refreshed_items:
                        if row.reserved_from_main > 0:
                            print(
    f"KEEP PackingOrderItem for item={row.id}, "
    f"reserved_from_main={row.reserved_from_main}"
)
                            main_product_for_packing = None
                            if main_warehouse and row.resolved_sku:
                                main_product_for_packing = Product.objects.select_for_update().filter(
                                    sku=row.resolved_sku,
                                    product_location=main_warehouse,
                                    company_id=user_company.id
                                ).first()

                            packing_item, _ = PackingOrderItem.objects.get_or_create(
                                packing_order=packing_order,
                                sales_order_item=row,
                                defaults={
                                    'product': main_product_for_packing,
                                    'quantity_required': row.reserved_from_main,
                                    'quantity_scanned': 0,
                                    'company': user_company
                                },
                            )
                            packing_item.quantity_required = row.reserved_from_main
                            if packing_item.quantity_scanned > row.reserved_from_main:
                                packing_item.quantity_scanned = row.reserved_from_main
                            packing_item.product = main_product_for_packing
                            packing_item.save(update_fields=['quantity_required', 'quantity_scanned', 'product'])
                        else:
                            print(
    f"DELETE PackingOrderItem for item={row.id}, "
    f"reserved_from_main={row.reserved_from_main}"
)
                            PackingOrderItem.objects.filter(
                                packing_order=packing_order,
                                sales_order_item=row,
                                company_id=user_company.id
                            ).delete()

            if new_status == SalesOrder.SalesOrderStatus.DELIVERED:
                # product FK jest nullable (SET_NULL), więc przy FOR UPDATE
                # nie możemy dokładać select_related('product') na PostgreSQL.
                final_items = list(
                    SalesOrderItem.objects.select_for_update().filter(order=order, company_id=user_company.id)
                )

                # Delivery can be finalized only for fully reserved quantities.
                for final_item in final_items:
                    # Używamy snapshotu SKU (resolved_sku), bo produkt mógł zostać usunięty,
                    # ale historia pozycji zamówienia nadal musi być czytelna.
                    sku = final_item.resolved_sku
                    if not sku:
                        error_msg = (
                            f"Cannot set order {order.order_number} to DELIVERED. "
                            'One or more items are missing product SKU data.'
                        )
                        messages.error(request, error_msg)
                        return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)

                    if (final_item.reserved_from_assigned + final_item.reserved_from_main) < final_item.quantity:
                        error_msg = (
                            f"Cannot set order {order.order_number} to DELIVERED. "
                            f"SKU {sku} is not fully reserved."
                        )
                        messages.error(request, error_msg)
                        return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)

                main_already_deducted = bool(packing_order and packing_order.stock_deducted)

                for final_item in final_items:
                    sku = final_item.resolved_sku
                    assigned_qty = final_item.reserved_from_assigned
                    main_qty = final_item.reserved_from_main

                    if assigned_qty > 0:
                        assigned_candidates = Product.objects.select_for_update().filter(sku=sku, company_id=user_company.id)
                        if main_warehouse:
                            assigned_candidates = assigned_candidates.exclude(product_location=main_warehouse)

                        assigned_candidates = list(assigned_candidates)

                        if assigned_warehouse:
                            assigned_candidates.sort(
                                key=lambda p: (
                                    0 if p.product_location_id == assigned_warehouse.id else 1,
                                    -p.reserved_quantity,
                                )
                            )
                        else:
                            assigned_candidates.sort(key=lambda p: -p.reserved_quantity)

                        remaining_assigned = assigned_qty
                        for assigned_product in assigned_candidates:
                            if remaining_assigned <= 0:
                                break
                            releasable_qty = min(remaining_assigned, assigned_product.reserved_quantity)
                            if releasable_qty <= 0:
                                continue

                            assigned_product.stock_quantity = max(assigned_product.stock_quantity - releasable_qty, 0)
                            assigned_product.reserved_quantity = max(
                                assigned_product.reserved_quantity - releasable_qty,
                                0,
                            )
                            assigned_product.save(update_fields=['stock_quantity', 'reserved_quantity'])
                            Logger.objects.create(
                                action=f"Stock deducted for SKU {sku} from ASSIGNED warehouse",
                                user=request.user,
                                details=f"Order {order.order_number} marked as DELIVERED. Deducted {releasable_qty} units of SKU {sku} from ASSIGNED warehouse.",
                                content_object=order
                            )
                            remaining_assigned -= releasable_qty

                    if main_qty > 0 and main_warehouse:
                        main_product = Product.objects.select_for_update().filter(
                            sku=sku,
                            product_location=main_warehouse,
                            company_id=user_company.id
                        ).first()
                        if main_product:
                            if not main_already_deducted:
                                main_product.stock_quantity = max(main_product.stock_quantity - main_qty, 0)
                            main_product.reserved_quantity = max(main_product.reserved_quantity - main_qty, 0)
                            main_product.save(update_fields=['stock_quantity', 'reserved_quantity'])
                            Logger.objects.create(
                                action=f"Stock deducted for SKU {sku} from MAIN warehouse",
                                user=request.user,
                                details=f"Order {order.order_number} marked as DELIVERED. Deducted {main_qty} units of SKU {sku} from MAIN warehouse.",
                                content_object=order
                            )
                    final_item.reserved_from_assigned = 0
                    final_item.reserved_from_main = 0
                    final_item.save(update_fields=['reserved_from_assigned', 'reserved_from_main'])

                if packing_order and not packing_order.stock_deducted:
                    packing_order.stock_deducted = True
                    packing_order.save(update_fields=['stock_deducted'])


            if packing_order and not packing_order.items_to_pack.exists():
                
                # packing_order.delete()
                if packing_order and not packing_order.items_to_pack.exists():
                    raise Exception(
                        f"PackingOrder {packing_order.id} would be deleted because it has no items_to_pack"
                    )

            order.calculate_value()

        for warning_msg in warnings:
            messages.warning(request, warning_msg)

        success_msg = f'Order {order.order_number} updated successfully.'
        messages.success(request, success_msg)
        return JsonResponse({'ok': True, 'message': success_msg, 'warnings': warnings})
    except Exception as e:
        error_msg = str(e)
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg, 'message': error_msg}, status=400)
    

@require_POST
@login_required
def delete_sales_order(request, order_id):
    user_company = get_object_or_404(Membership, user=request.user).company
    with transaction.atomic():
        order = SalesOrder.objects.filter(id=order_id, company_id=user_company.id).first()
        if not order:
            messages.error(request, 'Order not found.')
            return JsonResponse({'ok': False, 'error': 'Order not found.'}, status=404)
        
        if order.status not in ['DRAFT', 'IN WAREHOUSE']:
            messages.error(request, 'Only orders in DRAFT or IN WAREHOUSE status can be deleted.')
            return JsonResponse({'ok': False, 'error': 'Only orders in DRAFT or IN WAREHOUSE status can be deleted.'}, status=400)
        order_reserved_items = order.salesorderitem_set.filter(company_id=user_company.id)
        for item in order_reserved_items:
            if item.reserved_from_assigned and order.created_by_id:
                profile = UserProfile.objects.select_related('assigned_warehouse').filter(user_id=order.created_by_id).first()
                assigned_warehouse = profile.assigned_warehouse if profile else None
                if assigned_warehouse:
                    assigned_product = Product.objects.select_for_update().filter(
                        sku=item.resolved_sku,
                        product_location=assigned_warehouse,
                        company_id=user_company.id
                    ).first()
                    if assigned_product:
                        assigned_product.reserved_quantity = max(
                            assigned_product.reserved_quantity - item.reserved_from_assigned,
                            0,
                        )
                        assigned_product.save(update_fields=['reserved_quantity'])

            if item.reserved_from_main:
                main_warehouse = Warehouse.objects.filter(
                    warehouse_type=Warehouse.WarehouseType.MAIN,
                    company_id=user_company.id,
                ).first()
                if main_warehouse:
                    main_product = Product.objects.select_for_update().filter(
                        sku=item.resolved_sku,
                        product_location=main_warehouse,
                        company_id=user_company.id
                    ).first()
                    if main_product:
                        main_product.reserved_quantity = max(
                            main_product.reserved_quantity - item.reserved_from_main,
                            0,
                        )
                        main_product.save(update_fields=['reserved_quantity'])
        order.delete()
        messages.success(request, 'Order deleted successfully.')
    return JsonResponse({'ok': True, 'message': 'Order deleted successfully.'})


_TRANSITION_MAP = {
    'approve':        (SalesOrder.SalesOrderStatus.DRAFT,        SalesOrder.SalesOrderStatus.IN_WAREHOUSE),
    'mark_packed':    (SalesOrder.SalesOrderStatus.IN_WAREHOUSE, SalesOrder.SalesOrderStatus.PACKED),
    'assign_courier': (SalesOrder.SalesOrderStatus.PACKED,       SalesOrder.SalesOrderStatus.SHIPPED),
    'deliver':        (SalesOrder.SalesOrderStatus.SHIPPED,      SalesOrder.SalesOrderStatus.DELIVERED),
}

def _deduct_shipped_stock(order, user, company):
    """
    Deducts each order item's reserved quantities from the physical warehouse stock.
    Called on SHIPPED (items leave the building) and again on DELIVERED as a no-op
    safety net — zeroing reserved_from_* makes subsequent calls idempotent.
    """
    main_warehouse = Warehouse.objects.filter(
        warehouse_type=Warehouse.WarehouseType.MAIN,
        company=company,
    ).first()

    profile = UserProfile.objects.select_related('assigned_warehouse').filter(
        user=order.created_by
    ).first()
    assigned_warehouse = profile.assigned_warehouse if profile else None

    packing_order = PackingOrder.objects.filter(order=order, company=company).first()
    # Main warehouse stock may already be deducted by the packing scan flow.
    main_already_deducted = bool(packing_order and packing_order.stock_deducted)

    items = list(SalesOrderItem.objects.select_for_update().filter(order=order, company=company))

    for item in items:
        sku          = item.resolved_sku
        assigned_qty = item.reserved_from_assigned
        main_qty     = item.reserved_from_main

        # --- Assigned (store) warehouse ---
        if assigned_qty > 0:
            candidates = Product.objects.select_for_update().filter(sku=sku, company=company)
            if main_warehouse:
                candidates = candidates.exclude(product_location=main_warehouse)
            candidates = list(candidates)
            # Prefer the creator's assigned warehouse; within that, drain the most-reserved first.
            candidates.sort(key=lambda p: (
                0 if assigned_warehouse and p.product_location_id == assigned_warehouse.id else 1,
                -p.reserved_quantity,
            ))

            remaining = assigned_qty
            for product in candidates:
                if remaining <= 0:
                    break
                releasable = min(remaining, product.reserved_quantity)
                if releasable <= 0:
                    continue
                product.stock_quantity    = max(product.stock_quantity    - releasable, 0)
                product.reserved_quantity = max(product.reserved_quantity - releasable, 0)
                product.save(update_fields=['stock_quantity', 'reserved_quantity'])
                Logger.objects.create(
                    action=f'Stock deducted for SKU {sku} from ASSIGNED warehouse (order {order.order_number} shipped)',
                    user=user,
                    content_object=order,
                )
                remaining -= releasable

        # --- Main warehouse ---
        if main_qty > 0 and main_warehouse:
            main_product = Product.objects.select_for_update().filter(
                sku=sku,
                product_location=main_warehouse,
                company=company,
            ).first()
            if main_product:
                if not main_already_deducted:
                    main_product.stock_quantity = max(main_product.stock_quantity - main_qty, 0)
                main_product.reserved_quantity = max(main_product.reserved_quantity - main_qty, 0)
                main_product.save(update_fields=['stock_quantity', 'reserved_quantity'])
                Logger.objects.create(
                    action=f'Stock deducted for SKU {sku} from MAIN warehouse (order {order.order_number} shipped)',
                    user=user,
                    content_object=order,
                )

        item.reserved_from_assigned = 0
        item.reserved_from_main     = 0
        item.save(update_fields=['reserved_from_assigned', 'reserved_from_main'])

    if packing_order and not packing_order.stock_deducted:
        packing_order.stock_deducted = True
        packing_order.save(update_fields=['stock_deducted'])

@require_POST
@login_required
def transition_order(request, order_id):
    membership = get_object_or_404(Membership, user=request.user)

    if membership.role not in {Membership.Roles.ADMIN, Membership.Roles.MANAGER}:
        return JsonResponse({'ok': False, 'error': 'Permission denied.'}, status=403)

    order = get_object_or_404(SalesOrder, id=order_id, company=membership.company)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)

    action = data.get('action')
    if action not in _TRANSITION_MAP:
        return JsonResponse({'ok': False, 'error': 'Unknown action.'}, status=400)

    required_status, new_status = _TRANSITION_MAP[action]
    if order.status != required_status:
        return JsonResponse({
            'ok': False,
            'error': f'Order must be "{required_status}" to perform this action.',
        }, status=400)

    try:
        with transaction.atomic():
            update_fields = ['status']

            if action == 'assign_courier':
                carrier = data.get('carrier', '').strip()
                tracking_number = data.get('tracking_number', '').strip()
                if not carrier or not tracking_number:
                    return JsonResponse({'ok': False, 'error': 'Carrier and tracking number are required.'}, status=400)

                # Update the placeholder tracking row created at order creation rather
                # than inserting a second one (which would cause duplicates in the UI).
                tracking = Tracking.objects.filter(order=order).first()
                if tracking:
                    tracking.tracking_number = tracking_number
                    tracking.carrier         = carrier
                    tracking.status          = Tracking.TrackingStatus.SHIPPED
                    tracking.save(update_fields=['tracking_number', 'carrier', 'status'])
                else:
                    tracking = Tracking.objects.create(
                        tracking_number=tracking_number,
                        order=order,
                        carrier=carrier,
                        status=Tracking.TrackingStatus.SHIPPED,
                        created_by=request.user,
                        company=membership.company,
                    )
                order.tracking = tracking
                update_fields.append('tracking')

                # Items physically leave the warehouse — deduct reserved stock now.
                _deduct_shipped_stock(order, request.user, membership.company)

                # Packing order is no longer needed once the shipment is dispatched.
                PackingOrder.objects.filter(order=order, company=membership.company).delete()

            if action == 'deliver':
                # No-op if SHIPPED already zeroed the reservations; handles the
                # edge case where the order skipped the SHIPPED deduction path.
                _deduct_shipped_stock(order, request.user, membership.company)

            order.status = new_status
            order.save(update_fields=update_fields)

            _ACTION_MESSAGES = {
                'approve':        f'Order {order.order_number} approved — moved to In Warehouse.',
                'mark_packed':    f'Order {order.order_number} marked as Packed.',
                'assign_courier': f'Order {order.order_number} shipped via {data.get("carrier", "")} (tracking: {data.get("tracking_number", "")}).',
                'deliver':        f'Order {order.order_number} marked as Delivered.',
            }
            success_msg = _ACTION_MESSAGES.get(action, f'Order {order.order_number} updated.')
            messages.success(request, success_msg)

            Logger.objects.create(
                action=success_msg,
                user=request.user,
                content_object=order,
            )
    except Exception as e:
        error_msg = str(e)
        messages.error(request, error_msg)
        return JsonResponse({'ok': False, 'error': error_msg}, status=400)

    return JsonResponse({'ok': True, 'new_status': new_status, 'message': success_msg})