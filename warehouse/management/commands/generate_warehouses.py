"""
Management command: generate_warehouses
Usage:
    python manage.py generate_warehouses            # creates 4 warehouses with products
    python manage.py generate_warehouses --clear    # deletes generated ones first (by name prefix [GEN])
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from inventory.models import Product
from users.models import Membership
from warehouse.models import Warehouse


WAREHOUSES = [
    {
        'name':           '[GEN] Shop Warszawa Centrum',
        'warehouse_type': Warehouse.WarehouseType.SHOP,
        'address':        'ul. Marszałkowska 100',
        'city':           'Warszawa',
        'state':          'Masovian',
        'zip_code':       '00-001',
        'country':        'Poland',
        'notes':          'Flagship shop in the city centre. High footfall location.',
        'products': [
            ('EL-WAW-001', 'Wireless Earbuds Pro',       'electronics', 'A-01', 89.99,  60),
            ('EL-WAW-002', 'USB-C Hub 7-in-1',           'electronics', 'A-01', 49.99,  80),
            ('EL-WAW-003', 'Portable Phone Stand',       'electronics', 'A-02', 14.99, 120),
            ('EL-WAW-004', 'Screen Cleaning Kit',        'electronics', 'A-02', 9.99,  200),
            ('CL-WAW-001', 'Cotton T-Shirt White M',     'clothing',    'B-01', 19.99, 100),
            ('CL-WAW-002', 'Cotton T-Shirt Black M',     'clothing',    'B-01', 19.99,  90),
            ('CL-WAW-003', 'Slim Fit Jeans 32/32',       'clothing',    'B-02', 59.99,  45),
            ('CL-WAW-004', 'Hoodie Grey L',              'clothing',    'B-02', 49.99,  40),
            ('HM-WAW-001', 'Scented Soy Candle 200g',   'home',        'C-01', 12.99,  80),
            ('HM-WAW-002', 'Ceramic Coffee Mug 350ml',  'home',        'C-01', 8.99,  150),
        ],
    },
    {
        'name':           '[GEN] Shop Kraków Stare Miasto',
        'warehouse_type': Warehouse.WarehouseType.SHOP,
        'address':        'ul. Floriańska 22',
        'city':           'Kraków',
        'state':          'Lesser Poland',
        'zip_code':       '31-019',
        'country':        'Poland',
        'notes':          'Tourist-heavy location in the Old Town. Strong seasonal demand.',
        'products': [
            ('SP-KRK-001', 'Running Shoes Size 42',      'sports',      'A-01', 99.99,  30),
            ('SP-KRK-002', 'Yoga Mat 6mm',               'sports',      'A-01', 34.99,  50),
            ('SP-KRK-003', 'Water Bottle 750ml',         'sports',      'A-02', 19.99, 100),
            ('SP-KRK-004', 'Resistance Bands Set',       'sports',      'A-02', 24.99,  60),
            ('BK-KRK-001', 'Polish History Vol. 1',      'books',       'B-01', 29.99,  40),
            ('BK-KRK-002', 'Travel Guide: Kraków',       'books',       'B-01', 14.99,  70),
            ('BK-KRK-003', 'Learn Python in 30 Days',   'books',       'B-02', 39.99,  25),
            ('FD-KRK-001', 'Oscypek Cheese 200g',        'food',        'C-01', 7.99,   80),
            ('FD-KRK-002', 'Polish Honey 400g',          'food',        'C-01', 11.99,  60),
            ('FD-KRK-003', 'Dried Fruit Mix 250g',       'food',        'C-02', 5.99,  120),
        ],
    },
    {
        'name':           '[GEN] Shop Wrocław Rynek',
        'warehouse_type': Warehouse.WarehouseType.SHOP,
        'address':        'Rynek 15',
        'city':           'Wrocław',
        'state':          'Lower Silesia',
        'zip_code':       '50-101',
        'country':        'Poland',
        'notes':          'Market square location. Strong beauty and home category.',
        'products': [
            ('BE-WRO-001', 'Face Moisturiser SPF 30',    'beauty',      'A-01', 24.99,  90),
            ('BE-WRO-002', 'Micellar Water 400ml',       'beauty',      'A-01', 12.99, 110),
            ('BE-WRO-003', 'Vitamin C Serum 30ml',       'beauty',      'A-02', 34.99,  50),
            ('BE-WRO-004', 'Natural Lip Balm',           'beauty',      'A-02', 5.99,  200),
            ('HM-WRO-001', 'Bamboo Cutting Board',       'home',        'B-01', 18.99,  60),
            ('HM-WRO-002', 'Glass Food Storage 3-set',  'home',        'B-01', 29.99,  40),
            ('HM-WRO-003', 'Cotton Kitchen Towel 2pk',  'home',        'B-02', 9.99,  130),
            ('HM-WRO-004', 'Stainless Steel Thermos',   'home',        'B-02', 27.99,  55),
            ('AU-WRO-001', 'Car Phone Holder',           'automotive',  'C-01', 14.99,  80),
            ('AU-WRO-002', 'Microfibre Car Cloth 3pk',  'automotive',  'C-01', 8.99,  150),
        ],
    },
    {
        'name':           '[GEN] Distribution Centre Łódź',
        'warehouse_type': Warehouse.WarehouseType.SHOP,
        'address':        'ul. Piotrkowska 200',
        'city':           'Łódź',
        'state':          'Lodz',
        'zip_code':       '90-001',
        'country':        'Poland',
        'notes':          'Regional distribution hub. Supplies Warszawa and Wrocław shops.',
        'products': [
            ('DC-LDZ-001', 'Bubble Wrap Roll 50m',       'other',       'A-01', 15.99,  30),
            ('DC-LDZ-002', 'Cardboard Box 40x30x20',     'other',       'A-01', 1.49,  500),
            ('DC-LDZ-003', 'Packing Tape 50m',           'other',       'A-02', 3.99,  300),
            ('DC-LDZ-004', 'Stretch Film 500m',          'other',       'A-02', 22.99,  60),
            ('EL-LDZ-001', 'AA Batteries 8pk',           'electronics', 'B-01', 6.99,  400),
            ('EL-LDZ-002', 'AAA Batteries 8pk',          'electronics', 'B-01', 6.99,  350),
            ('EL-LDZ-003', 'Power Strip 4-socket',       'electronics', 'B-02', 19.99, 120),
            ('EL-LDZ-004', 'Extension Cable 5m',         'electronics', 'B-02', 12.99, 100),
            ('CL-LDZ-001', 'Plain White Socks 5pk',      'clothing',    'C-01', 12.99, 200),
            ('CL-LDZ-002', 'Black Work Gloves',          'clothing',    'C-01', 9.99,  180),
            ('FD-LDZ-001', 'Instant Coffee 200g',        'food',        'D-01', 8.99,  250),
            ('FD-LDZ-002', 'Energy Bar Box 12pk',        'food',        'D-01', 18.99, 100),
        ],
    },
]


class Command(BaseCommand):
    help = 'Generate 4 warehouses with products for development/testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete previously generated [GEN] warehouses (and their products) first.',
        )

    def handle(self, *args, **options):
        membership = Membership.objects.select_related('company', 'user').first()
        if not membership:
            raise CommandError('No Membership found. Create a company and user first.')

        company = membership.company
        user = membership.user
        self.stdout.write(f'Company: {company.name} | User: {user.username}')

        with transaction.atomic():
            if options['clear']:
                deleted, _ = Warehouse.objects.filter(
                    company=company,
                    name__startswith='[GEN]',
                ).delete()
                self.stdout.write(self.style.WARNING(
                    f'Deleted {deleted} previously generated warehouse(s) and their products.'
                ))

            created_wh = 0
            created_pr = 0
            skipped_wh = 0

            for wh_data in WAREHOUSES:
                products_data = wh_data.pop('products')

                warehouse, wh_created = Warehouse.objects.get_or_create(
                    name=wh_data['name'],
                    company=company,
                    defaults={**wh_data, 'created_by': user},
                )

                if wh_created:
                    created_wh += 1
                else:
                    skipped_wh += 1
                    wh_data['products'] = products_data
                    self.stdout.write(
                        self.style.WARNING(f'  Skipped (already exists): {warehouse.name}')
                    )
                    continue

                for sku, name, category, bin_loc, price, stock_qty in products_data:
                    _, pr_created = Product.objects.get_or_create(
                        sku=sku,
                        product_location=warehouse,
                        defaults=dict(
                            name=name,
                            category=category,
                            bin_location=bin_loc,
                            price=price,
                            stock_quantity=stock_qty,
                            created_by=user,
                            company=company,
                        ),
                    )
                    if pr_created:
                        created_pr += 1

                self.stdout.write(f'  Created: {warehouse.name} ({len(products_data)} products)')
                wh_data['products'] = products_data

        if skipped_wh:
            self.stdout.write(self.style.WARNING(
                f'{skipped_wh} warehouse(s) already existed and were skipped (use --clear to reset).'
            ))
        self.stdout.write(self.style.SUCCESS(
            f'Done — {created_wh} warehouses, {created_pr} products created.'
        ))