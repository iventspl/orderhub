"""
Management command: generate_test_orders
Usage:
    python manage.py generate_test_orders            # creates 30 orders
    python manage.py generate_test_orders --count 50
    python manage.py generate_test_orders --clear    # deletes existing test orders first

Creates SalesOrders (and PackingOrders where applicable) spread across all statuses.
Signals are disconnected during creation so stock levels are not affected.
"""

import random
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.utils import timezone

from customers.models import Customer
from inventory.models import Product
from packing.models import PackingOrder, PackingOrderItem
from packing.signals import (
    validate_before_marking_packed,
    reserve_items_and_prepare_packing,
    deduct_main_stock_when_shipped,
    remove_packing_order_on_cancellation_or_delivered,
)
from sales.models import SalesOrder, SalesOrderItem
from users.models import Membership
from warehouse.models import Warehouse


FIRST_NAMES = ['Anna', 'Piotr', 'Katarzyna', 'Marek', 'Agnieszka', 'Tomasz', 'Monika', 'Krzysztof']
LAST_NAMES = ['Kowalski', 'Nowak', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kaminski', 'Lewandowski', 'Zielinski']

STATUS_WEIGHTS = [
    (SalesOrder.SalesOrderStatus.DRAFT,        10),
    (SalesOrder.SalesOrderStatus.IN_WAREHOUSE,  15),
    (SalesOrder.SalesOrderStatus.PACKED,        10),
    (SalesOrder.SalesOrderStatus.SHIPPED,       20),
    (SalesOrder.SalesOrderStatus.DELIVERED,     25),
    (SalesOrder.SalesOrderStatus.PAID,          10),
    (SalesOrder.SalesOrderStatus.CANCELLED,     10),
]

PACKING_STATUSES_FOR_ORDER = {
    SalesOrder.SalesOrderStatus.IN_WAREHOUSE:  PackingOrder.PackingStatus.PENDING,
    SalesOrder.SalesOrderStatus.PACKED:        PackingOrder.PackingStatus.PACKED,
    SalesOrder.SalesOrderStatus.SHIPPED:       PackingOrder.PackingStatus.SHIPPED,
    SalesOrder.SalesOrderStatus.DELIVERED:     PackingOrder.PackingStatus.SHIPPED,
}


def _weighted_choice(weighted_list):
    population = [item for item, weight in weighted_list for _ in range(weight)]
    return random.choice(population)


class Command(BaseCommand):
    help = 'Generate test SalesOrders and PackingOrders for development.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=30, help='Number of orders to create (default: 30)')
        parser.add_argument('--clear', action='store_true', help='Delete previously generated test orders first')

    def handle(self, *args, **options):
        count = options['count']

        # ── Disconnect all packing/sales signals ───────────────────────────────
        pre_save.disconnect(validate_before_marking_packed, sender=PackingOrder)
        post_save.disconnect(reserve_items_and_prepare_packing, sender=SalesOrderItem)
        post_save.disconnect(deduct_main_stock_when_shipped, sender=PackingOrder)
        post_save.disconnect(remove_packing_order_on_cancellation_or_delivered, sender=SalesOrder)

        try:
            self._run(count, options['clear'])
        finally:
            # Always reconnect signals
            pre_save.connect(validate_before_marking_packed, sender=PackingOrder)
            post_save.connect(reserve_items_and_prepare_packing, sender=SalesOrderItem)
            post_save.connect(deduct_main_stock_when_shipped, sender=PackingOrder)
            post_save.connect(remove_packing_order_on_cancellation_or_delivered, sender=SalesOrder)

    def _run(self, count, clear):
        # ── Get company & user ─────────────────────────────────────────────────
        membership = Membership.objects.select_related('company', 'user').first()
        if not membership:
            raise CommandError('No Membership found. Create a company and user first.')

        company = membership.company
        user = membership.user
        self.stdout.write(f'Using company: {company.name}, user: {user.username}')

        # ── Get or create customers ────────────────────────────────────────────
        customers = list(Customer.objects.filter(company=company)[:20])
        if len(customers) < 5:
            self.stdout.write('Creating test customers...')
            for i in range(10):
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                email = f'testcust{i}_{random.randint(1000,9999)}@example.com'
                c = Customer.objects.create(
                    first_name=first,
                    last_name=last,
                    email=email,
                    company=company,
                    created_by=user,
                )
                customers.append(c)

        # ── Get products from MAIN warehouse ───────────────────────────────────
        main_warehouse = Warehouse.objects.filter(
            warehouse_type=Warehouse.WarehouseType.MAIN,
            company=company,
        ).first()
        if not main_warehouse:
            raise CommandError('No MAIN warehouse found for this company.')

        products = list(
            Product.objects.filter(
                company=company,
                product_location=main_warehouse,
                stock_quantity__gt=0,
            )[:30]
        )
        if not products:
            raise CommandError(
                'No products with stock in MAIN warehouse. Add some products first.'
            )
        self.stdout.write(f'Found {len(products)} products in MAIN warehouse.')

        # ── Optionally clear test orders ───────────────────────────────────────
        if clear:
            deleted, _ = SalesOrder.objects.filter(
                company=company,
                notes__startswith='[TEST]',
            ).delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing test orders.'))

        # ── Create orders ──────────────────────────────────────────────────────
        created_orders = 0
        created_packing = 0

        with transaction.atomic():
            for i in range(count):
                order_status = _weighted_choice(STATUS_WEIGHTS)
                customer = random.choice(customers)
                num_items = random.randint(1, min(3, len(products)))
                chosen_products = random.sample(products, num_items)

                # Create SalesOrder directly (bypass auto-number, set it manually after pk)
                order = SalesOrder(
                    customer=customer,
                    status=order_status,
                    company=company,
                    created_by=user,
                    notes='[TEST] Auto-generated test order',
                    payment_method=random.choice([
                        SalesOrder.SalesPaymentMethod.ON_DELIVERY,
                        SalesOrder.SalesPaymentMethod.NET_7,
                        SalesOrder.SalesPaymentMethod.PREPAID,
                    ]),
                )
                order.save()

                # Create items
                total_value = 0
                for product in chosen_products:
                    qty = random.randint(1, 3)
                    item = SalesOrderItem(
                        order=order,
                        product=product,
                        product_sku=product.sku,
                        product_name=product.name,
                        quantity=qty,
                        reserved_from_main=qty,
                        company=company,
                    )
                    item.save()
                    total_value += (product.price or 0) * qty

                SalesOrder.objects.filter(pk=order.pk).update(value=total_value)

                # Create PackingOrder where applicable
                packing_status = PACKING_STATUSES_FOR_ORDER.get(order_status)
                if packing_status:
                    po = PackingOrder.objects.create(
                        order=order,
                        status=packing_status,
                        company=company,
                        packed_by=user if packing_status in (
                            PackingOrder.PackingStatus.PACKED,
                            PackingOrder.PackingStatus.SHIPPED,
                        ) else None,
                        packed_on=timezone.now() if packing_status in (
                            PackingOrder.PackingStatus.PACKED,
                            PackingOrder.PackingStatus.SHIPPED,
                        ) else None,
                        stock_deducted=packing_status == PackingOrder.PackingStatus.SHIPPED,
                        is_packed=packing_status in (
                            PackingOrder.PackingStatus.PACKED,
                            PackingOrder.PackingStatus.SHIPPED,
                        ),
                    )

                    items_qs = SalesOrderItem.objects.filter(order=order)
                    for item in items_qs:
                        scanned = item.quantity if packing_status in (
                            PackingOrder.PackingStatus.PACKED,
                            PackingOrder.PackingStatus.SHIPPED,
                        ) else random.randint(0, item.quantity)
                        PackingOrderItem.objects.create(
                            packing_order=po,
                            sales_order_item=item,
                            product=item.product,
                            product_sku=item.product_sku,
                            product_name=item.product_name,
                            quantity_required=item.quantity,
                            quantity_scanned=scanned,
                            company=company,
                        )

                    created_packing += 1

                created_orders += 1

        self.stdout.write(self.style.SUCCESS(
            f'Created {created_orders} orders ({created_packing} with PackingOrders).'
        ))
