from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Greatest
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from inventory.models import Product
from sales.models import SalesOrderItem, SalesOrder
from users.models import UserProfile
from warehouse.models import Warehouse

from .models import PackingOrder, PackingOrderItem


@receiver(pre_save, sender=PackingOrder)
def validate_before_marking_packed(sender, instance, **kwargs):
    if not instance.pk:
        return
    if instance.status != PackingOrder.PackingStatus.PACKED:
        return

    # PackingOrder ma bezpośrednio company_id — nie potrzebujemy Membership
    company_id = instance.company_id

    previous_status = PackingOrder.objects.filter(pk=instance.pk, company_id=company_id).values_list('status', flat=True).first()
    if previous_status == PackingOrder.PackingStatus.PACKED:
        return

    if instance.is_partial:
        return

    has_items = PackingOrderItem.objects.filter(packing_order=instance, company_id=company_id).exists()
    has_incomplete_items = PackingOrderItem.objects.filter(
        packing_order=instance,
        quantity_scanned__lt=F('quantity_required'),
        company_id=company_id,
    ).exists()
    has_missing_product = PackingOrderItem.objects.filter(
        packing_order=instance,
        product__isnull=True,
        company_id=company_id,
    ).exists()

    if not has_items or has_incomplete_items:
        raise ValidationError('Cannot set PackingOrder to PACKED until all required quantities are scanned.')
    if has_missing_product:
        raise ValidationError('Cannot set PackingOrder to PACKED because one or more items have deleted products.')


@receiver(post_save, sender=SalesOrderItem)
def reserve_items_and_prepare_packing(sender, instance, created, **kwargs):
    if not created:
        return

    company_id = instance.company_id
    requested_qty = instance.quantity
    if requested_qty <= 0:
        return

    with transaction.atomic():
        order = instance.order
        assigned_warehouse = None

        if order.created_by_id:
            profile = UserProfile.objects.select_related('assigned_warehouse').filter(user=order.created_by).first()
            if profile and profile.assigned_warehouse and profile.assigned_warehouse.company_id == company_id:
                assigned_warehouse = profile.assigned_warehouse

        main_warehouse = Warehouse.objects.filter(
            warehouse_type=Warehouse.WarehouseType.MAIN,
            company_id=company_id,
        ).first()
        if assigned_warehouse and main_warehouse and assigned_warehouse.id == main_warehouse.id:
            main_warehouse = None

        reserved_assigned = 0
        reserved_main = 0
        remaining_qty = requested_qty

        # Reserve from assigned warehouse first.
        if assigned_warehouse:
            assigned_product = Product.objects.select_for_update().filter(
                sku=instance.product.sku,
                product_location=assigned_warehouse,
                company_id=company_id,
            ).first()
            if assigned_product:
                available_assigned = max(assigned_product.stock_quantity - assigned_product.reserved_quantity, 0)
                reserved_assigned = min(available_assigned, remaining_qty)
                if reserved_assigned:
                    assigned_product.reserved_quantity += reserved_assigned
                    assigned_product.save(update_fields=['reserved_quantity'])
                    remaining_qty -= reserved_assigned

        # Reserve missing part from MAIN warehouse and create PackingOrder entries.
        if remaining_qty > 0 and main_warehouse:
            # Use select_for_update to lock the product row in MAIN warehouse during reservation
            main_product = Product.objects.select_for_update().filter(
                sku=instance.product.sku,
                product_location=main_warehouse,
                company_id=company_id,
            ).first()
            if main_product:
                # Calculate how much can be reserved from MAIN warehouse based on available stock and already reserved quantity
                available_main = max(main_product.stock_quantity - main_product.reserved_quantity, 0)
                reserved_main = min(available_main, remaining_qty)
                if reserved_main:
                    main_product.reserved_quantity += reserved_main
                    main_product.save(update_fields=['reserved_quantity'])
                    remaining_qty -= reserved_main

                    packing_order, _ = PackingOrder.objects.get_or_create(
                        order=order,
                        defaults={'status': PackingOrder.PackingStatus.PENDING, 'company_id': company_id},
                    )
                    PackingOrderItem.objects.update_or_create(
                        packing_order=packing_order,
                        sales_order_item=instance,
                        defaults={
                            'product': main_product,
                            'quantity_required': reserved_main,
                            'company_id': company_id,
                        },
                    )

        if remaining_qty > 0:
            raise ValidationError(
                f'Not enough stock for SKU {instance.resolved_sku}. '
                f'Available total (assigned + main): {requested_qty - remaining_qty}, '
                f'Requested: {requested_qty}'
            )

        SalesOrderItem.objects.filter(pk=instance.pk).update(
            reserved_from_assigned=reserved_assigned,
            reserved_from_main=reserved_main,
        )


@receiver(post_save, sender=PackingOrder)
def deduct_main_stock_when_shipped(sender, instance, created, **kwargs):
    if created:
        return
    if instance.status != PackingOrder.PackingStatus.SHIPPED:
        return
    if instance.stock_deducted:
        return

    with transaction.atomic():
        # Analogicznie: brak select_related('product') przy FOR UPDATE,
        # bo product może być NULL po usunięciu produktu z magazynu.
        items = PackingOrderItem.objects.select_for_update().filter(
            packing_order=instance,
            company_id=instance.company_id,
        )
        for item in items:
            product = item.product
            qty = item.quantity_required
            if qty <= 0:
                continue
            # Gdy produkt został usunięty (SET_NULL), nie próbujemy zdejmować stocku.
            if not product:
                continue

            product.stock_quantity = max(product.stock_quantity - qty, 0)
            product.reserved_quantity = max(product.reserved_quantity - qty, 0)
            product.save(update_fields=['stock_quantity', 'reserved_quantity'])

        PackingOrder.objects.filter(pk=instance.pk, company_id=instance.company_id).update(
            stock_deducted=True,
            is_packed=True,
            packed_on=instance.packed_on or timezone.now(),
        )


@receiver(post_save, sender=SalesOrder)
def remove_packing_order_on_cancellation_or_delivered(sender, instance, created, **kwargs):
    print(
    f"SalesOrder signal fired. Order={instance.id} status={instance.status}"
    )
    if created:
        return
    if instance.status not in [SalesOrder.SalesOrderStatus.CANCELLED, SalesOrder.SalesOrderStatus.DELIVERED]:
        return

    # PackingOrder.order jest OneToOneField → nie potrzebujemy Membership do wyszukania
    packing_order = PackingOrder.objects.filter(order=instance).first()
    if not packing_order:
        return

    # SHIPPED → nic nie robimy, zlecenie jest już zamknięte
    if packing_order.status == PackingOrder.PackingStatus.SHIPPED:
        return

    # PACKED → nie usuwamy, tylko oznaczamy jako SHIPPED
    # → odpali sygnał deduct_main_stock_when_shipped (zdejmie stock + reserved)
    if packing_order.status == PackingOrder.PackingStatus.PACKED:
        packing_order.status = PackingOrder.PackingStatus.SHIPPED
        packing_order.save(update_fields=['status'])
        return

    # PENDING / IN_PROGRESS → zwolnij reserved_quantity i usuń zlecenie
    with transaction.atomic():
        items = PackingOrderItem.objects.select_related('product').filter(
            packing_order=packing_order,
        )
        for item in items:
            if item.product and item.quantity_required > 0:
                Product.objects.filter(pk=item.product_id).update(
                    reserved_quantity=Greatest(F('reserved_quantity') - item.quantity_required, 0)
                )
        packing_order.delete()