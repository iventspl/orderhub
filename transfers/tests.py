from django.test import TestCase
from django.urls import reverse

from inventory.models import Product
from users.models import Company, Membership, User, UserProfile
from warehouse.models import Warehouse

from .forms import TransferProductFormSet
from .models import Transfer


class CreateTransferTests(TestCase):
	def setUp(self):
		self.company = Company.objects.create(name='SuperVista Test')
		self.user = User.objects.create_user(username='transfer-user', password='secret123')
		Membership.objects.create(user=self.user, company=self.company, role=Membership.Roles.MANAGER)
		self.source_warehouse = Warehouse.objects.create(
			name='Source',
			address='One',
			city='City',
			state='State',
			zip_code='00-000',
			country='PL',
			warehouse_type=Warehouse.WarehouseType.SHOP,
			created_by=self.user,
			company=self.company,
		)
		self.destination_warehouse = Warehouse.objects.create(
			name='Destination',
			address='Two',
			city='City',
			state='State',
			zip_code='00-000',
			country='PL',
			warehouse_type=Warehouse.WarehouseType.MAIN,
			created_by=self.user,
			company=self.company,
		)
		UserProfile.objects.create(user=self.user, email='transfer-user@example.com', assigned_warehouse=self.source_warehouse)
		self.product_one = Product.objects.create(
			name='Alternator',
			sku='ALT-001',
			description='Alternator',
			price='350.00',
			stock_quantity=20,
			reserved_quantity=0,
			product_location=self.source_warehouse,
			created_by=self.user,
			company=self.company,
			category=Product.ProductCategory.AUTOMOTIVE,
		)
		self.product_two = Product.objects.create(
			name='Brake Pads',
			sku='BRK-002',
			description='Brake Pads',
			price='120.00',
			stock_quantity=15,
			reserved_quantity=0,
			product_location=self.source_warehouse,
			created_by=self.user,
			company=self.company,
			category=Product.ProductCategory.AUTOMOTIVE,
		)

	def test_create_transfer_handles_main_product_and_extra_formset_products(self):
		self.client.force_login(self.user)
		formset = TransferProductFormSet(instance=Transfer(), form_kwargs={'company_id': self.company.id})
		prefix = formset.prefix

		response = self.client.post(
			reverse('transfers:create_transfer'),
			{
				'source_warehouse': self.source_warehouse.id,
				'destination_warehouse': self.destination_warehouse.id,
				'product': self.product_one.id,
				'quantity': 4,
				'notes': 'Batch transfer',
				f'{prefix}-TOTAL_FORMS': 1,
				f'{prefix}-INITIAL_FORMS': 0,
				f'{prefix}-MIN_NUM_FORMS': 0,
				f'{prefix}-MAX_NUM_FORMS': 1000,
				f'{prefix}-0-product': self.product_two.id,
				f'{prefix}-0-quantity': 3,
			},
		)

		self.assertEqual(response.status_code, 302)
		transfer = Transfer.objects.get()
		self.assertEqual(transfer.transfer_products.count(), 2)

		self.product_one.refresh_from_db()
		self.product_two.refresh_from_db()
		self.assertEqual(self.product_one.stock_quantity, 16)
		self.assertEqual(self.product_two.stock_quantity, 12)

		destination_product_one = Product.objects.get(
			company=self.company,
			product_location=self.destination_warehouse,
			sku='ALT-001',
		)
		destination_product_two = Product.objects.get(
			company=self.company,
			product_location=self.destination_warehouse,
			sku='BRK-002',
		)
		self.assertEqual(destination_product_one.stock_quantity, 4)
		self.assertEqual(destination_product_two.stock_quantity, 3)
