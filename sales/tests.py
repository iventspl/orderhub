from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase

from customers.models import Customer
from inventory.models import Product
from users.models import Company, Membership, User, UserProfile
from warehouse.models import Warehouse

from .models import SalesOrder, SalesOrderItem


class SalesOrderStockReservationTests(TestCase):
	def setUp(self):
		self.company = Company.objects.create(name='Test Company')
		self.user = User.objects.create_user(username='sales-user', password='test-password')
		Membership.objects.create(
			user=self.user,
			company=self.company,
			role=Membership.Roles.EMPLOYEE,
		)
		self.warehouse = Warehouse.objects.create(
			name='Main',
			address='1 Test Street',
			city='Test City',
			state='Test State',
			zip_code='00000',
			country='Test Country',
			warehouse_type=Warehouse.WarehouseType.MAIN,
			created_by=self.user,
			company=self.company,
		)
		UserProfile.objects.create(
			user=self.user,
			email='sales-user@example.com',
			assigned_warehouse=self.warehouse,
		)
		self.product = Product.objects.create(
			name='Test Product',
			sku='TEST-001',
			price='10.00',
			stock_quantity=100,
			product_location=self.warehouse,
			created_by=self.user,
			company=self.company,
		)
		self.customer = Customer.objects.create(
			first_name='Test',
			last_name='Customer',
			email='customer@example.com',
			created_by=self.user,
			company=self.company,
		)

	def create_order(self, quantity):
		order = SalesOrder.objects.create(
			customer=self.customer,
			created_by=self.user,
			company=self.company,
		)
		SalesOrderItem.objects.create(
			order=order,
			product=self.product,
			quantity=quantity,
			company=self.company,
		)
		return order

	def test_rejects_order_when_existing_reservation_leaves_too_little_stock(self):
		self.create_order(50)

		with self.assertRaisesMessage(ValidationError, 'Not enough stock for SKU TEST-001'):
			with transaction.atomic():
				self.create_order(52)

		self.product.refresh_from_db()
		self.assertEqual(self.product.reserved_quantity, 50)
		self.assertEqual(SalesOrderItem.objects.count(), 1)
