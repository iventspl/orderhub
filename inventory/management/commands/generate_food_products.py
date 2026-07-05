"""
Management command: generate_food_products
Usage:
    python manage.py generate_food_products            # creates ~50 products in MAIN warehouse
    python manage.py generate_food_products --clear    # deletes previously generated ones first
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from inventory.models import Product
from users.models import Membership
from warehouse.models import Warehouse


FOOD_PRODUCTS = [
    # (name, sku, price, stock_quantity, bin_location, description)
    ('Whole Milk 1L',               'FOOD-001', 1.49,  200, 'A-01', 'Fresh full-fat whole milk, 1 litre carton.'),
    ('Semi-Skimmed Milk 1L',        'FOOD-002', 1.39,  180, 'A-01', 'Semi-skimmed milk, 1 litre carton.'),
    ('Butter 200g',                 'FOOD-003', 2.99,  150, 'A-02', 'Unsalted creamery butter block, 200 g.'),
    ('Salted Butter 200g',          'FOOD-004', 2.99,  130, 'A-02', 'Salted creamery butter block, 200 g.'),
    ('Cheddar Cheese 400g',         'FOOD-005', 4.49,  100, 'A-03', 'Mature cheddar cheese block, 400 g.'),
    ('Mozzarella 125g',             'FOOD-006', 1.89,  120, 'A-03', 'Fresh mozzarella ball in brine, 125 g.'),
    ('Greek Yoghurt 500g',          'FOOD-007', 2.49,   90, 'A-04', 'Full-fat Greek-style strained yoghurt.'),
    ('Natural Yoghurt 400g',        'FOOD-008', 1.59,  110, 'A-04', 'Plain natural yoghurt, no added sugar.'),
    ('Free-Range Eggs 6pk',         'FOOD-009', 2.79,  200, 'A-05', 'Medium free-range eggs, pack of 6.'),
    ('Free-Range Eggs 12pk',        'FOOD-010', 4.99,  160, 'A-05', 'Medium free-range eggs, pack of 12.'),
    ('White Bread 800g',            'FOOD-011', 1.29,  250, 'B-01', 'Soft sliced white bread loaf, 800 g.'),
    ('Wholemeal Bread 800g',        'FOOD-012', 1.49,  200, 'B-01', 'Sliced wholemeal bread loaf, 800 g.'),
    ('Sourdough Loaf 600g',         'FOOD-013', 3.49,   80, 'B-02', 'Artisan sourdough bread, 600 g.'),
    ('Baguette',                    'FOOD-014', 0.89,  100, 'B-02', 'Crispy white baguette, approx. 250 g.'),
    ('Rolled Oats 1kg',             'FOOD-015', 1.99,  140, 'B-03', 'Wholegrain rolled oats for porridge.'),
    ('Chicken Breast 500g',         'FOOD-016', 4.99,   80, 'C-01', 'Boneless skinless chicken breast fillets.'),
    ('Chicken Thighs 1kg',          'FOOD-017', 5.49,   70, 'C-01', 'Bone-in skin-on chicken thighs, 1 kg.'),
    ('Beef Mince 500g',             'FOOD-018', 4.79,   90, 'C-02', 'Lean 5% fat beef mince, 500 g.'),
    ('Pork Sausages 400g',          'FOOD-019', 3.29,  110, 'C-02', 'Traditional pork sausages, pack of 6.'),
    ('Salmon Fillet 300g',          'FOOD-020', 6.99,   60, 'C-03', 'Atlantic salmon fillet portions, 300 g.'),
    ('Tuna in Spring Water 145g',   'FOOD-021', 1.09,  300, 'C-04', 'Canned tuna chunks in spring water.'),
    ('Baked Beans 400g',            'FOOD-022', 0.59,  400, 'D-01', 'Haricot beans in tomato sauce, 400 g tin.'),
    ('Chopped Tomatoes 400g',       'FOOD-023', 0.69,  350, 'D-01', 'Italian chopped tomatoes, 400 g tin.'),
    ('Coconut Milk 400ml',          'FOOD-024', 1.49,  200, 'D-02', 'Full-fat coconut milk, 400 ml tin.'),
    ('Chickpeas 400g',              'FOOD-025', 0.79,  250, 'D-02', 'Cooked chickpeas in water, 400 g tin.'),
    ('Red Kidney Beans 400g',       'FOOD-026', 0.79,  220, 'D-03', 'Cooked red kidney beans in water.'),
    ('Long Grain White Rice 1kg',   'FOOD-027', 1.79,  180, 'D-03', 'Easy-cook long grain white rice, 1 kg.'),
    ('Basmati Rice 1kg',            'FOOD-028', 2.49,  150, 'D-04', 'Fragrant basmati rice, 1 kg bag.'),
    ('Penne Pasta 500g',            'FOOD-029', 1.19,  200, 'D-04', 'Dried penne rigate pasta, 500 g.'),
    ('Spaghetti 500g',              'FOOD-030', 1.09,  220, 'D-05', 'Dried spaghetti No. 5, 500 g.'),
    ('Fusilli 500g',                'FOOD-031', 1.19,  180, 'D-05', 'Dried fusilli pasta twists, 500 g.'),
    ('Olive Oil Extra Virgin 500ml','FOOD-032', 5.99,  100, 'E-01', 'Cold-pressed extra virgin olive oil.'),
    ('Sunflower Oil 1L',            'FOOD-033', 2.49,  120, 'E-01', 'Refined sunflower cooking oil, 1 litre.'),
    ('Plain Flour 1kg',             'FOOD-034', 1.09,  160, 'E-02', 'Plain white wheat flour, 1 kg bag.'),
    ('Self-Raising Flour 1kg',      'FOOD-035', 1.19,  130, 'E-02', 'Self-raising flour with baking powder.'),
    ('Granulated Sugar 1kg',        'FOOD-036', 1.29,  170, 'E-03', 'White granulated cane sugar, 1 kg.'),
    ('Icing Sugar 500g',            'FOOD-037', 1.09,  100, 'E-03', 'Fine icing sugar for baking and decoration.'),
    ('Honey 340g',                  'FOOD-038', 3.49,   80, 'E-04', 'Clear runny honey, 340 g jar.'),
    ('Strawberry Jam 340g',         'FOOD-039', 1.99,   90, 'E-04', 'Strawberry preserve, 340 g glass jar.'),
    ('Tomato Ketchup 570g',         'FOOD-040', 2.29,  110, 'F-01', 'Classic tomato ketchup, 570 g bottle.'),
    ('Dijon Mustard 200g',          'FOOD-041', 1.89,   80, 'F-01', 'Smooth Dijon-style mustard, 200 g jar.'),
    ('Soy Sauce 150ml',             'FOOD-042', 1.49,  100, 'F-02', 'Dark soy sauce, 150 ml bottle.'),
    ('Vegetable Stock Cubes 8pk',   'FOOD-043', 0.99,  200, 'F-02', 'Vegetable bouillon stock cubes, pack of 8.'),
    ('Chicken Stock Cubes 10pk',    'FOOD-044', 0.99,  200, 'F-02', 'Chicken flavour stock cubes, pack of 10.'),
    ('Ground Black Pepper 50g',     'FOOD-045', 1.29,  150, 'F-03', 'Coarsely ground black pepper, 50 g tin.'),
    ('Fine Sea Salt 750g',          'FOOD-046', 0.89,  180, 'F-03', 'Fine sea salt for cooking and seasoning.'),
    ('Paprika 40g',                 'FOOD-047', 1.39,  120, 'F-04', 'Sweet smoked paprika powder, 40 g.'),
    ('Cumin Ground 35g',            'FOOD-048', 1.29,  100, 'F-04', 'Ground cumin spice, 35 g jar.'),
    ('Orange Juice 1L',             'FOOD-049', 1.99,  140, 'G-01', 'Freshly squeezed orange juice, 1 litre.'),
    ('Apple Juice 1L',              'FOOD-050', 1.79,  130, 'G-01', 'Cloudy pressed apple juice, 1 litre.'),
]


class Command(BaseCommand):
    help = 'Generate 50 food products in the MAIN warehouse for development/testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete previously generated food products (SKU FOOD-*) before creating new ones.',
        )

    def handle(self, *args, **options):
        membership = Membership.objects.select_related('company', 'user').first()
        if not membership:
            raise CommandError('No Membership found. Create a company and user first.')

        company = membership.company
        user = membership.user
        self.stdout.write(f'Company: {company.name} | User: {user.username}')

        main_warehouse = Warehouse.objects.filter(
            warehouse_type=Warehouse.WarehouseType.MAIN,
            company=company,
        ).first()
        if not main_warehouse:
            raise CommandError('No MAIN warehouse found for this company. Create one first.')

        self.stdout.write(f'MAIN warehouse: {main_warehouse.name}')

        with transaction.atomic():
            if options['clear']:
                deleted, _ = Product.objects.filter(
                    company=company,
                    product_location=main_warehouse,
                    sku__startswith='FOOD-',
                ).delete()
                self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing FOOD-* products.'))

            created = 0
            skipped = 0
            for name, sku, price, stock_qty, bin_loc, description in FOOD_PRODUCTS:
                _, was_created = Product.objects.get_or_create(
                    sku=sku,
                    product_location=main_warehouse,
                    defaults=dict(
                        name=name,
                        category=Product.ProductCategory.FOOD,
                        description=description,
                        price=price,
                        stock_quantity=stock_qty,
                        bin_location=bin_loc,
                        created_by=user,
                        company=company,
                    ),
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        if skipped:
            self.stdout.write(self.style.WARNING(
                f'{skipped} product(s) already existed and were skipped (use --clear to reset).'
            ))
        self.stdout.write(self.style.SUCCESS(f'Created {created} food products in "{main_warehouse.name}".'))
