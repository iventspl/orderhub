from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer
from inventory.models import Product
from packing.models import PackingOrder, PackingOrderItem
from sales.models import SalesOrder, SalesOrderItem
from tracking.models import Tracking
from users.models import UserProfile
from warehouse.models import Warehouse


class CompletePackingViewTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username='packer',
			email='packer@example.com',
			password='testpass123',
		)

		self.main_warehouse = Warehouse.objects.create(
			name='Main Warehouse',
			address='Main 1',
			city='Berlin',
			state='BE',
			zip_code='10000',
			country='DE',
			warehouse_type=Warehouse.WarehouseType.MAIN,
			created_by=self.user,
		)

		self.product = Product.objects.create(
			name='Lens Kit',
			sku='LK-001',
			price='99.99',
			reserved_quantity=0,
			stock_quantity=10,
			product_location=self.main_warehouse,
			created_by=self.user,
		)

		self.customer = Customer.objects.create(
			first_name='Jan',
			last_name='Kowalski',
			email='jan@example.com',
			created_by=self.user,
		)

		self.order = SalesOrder.objects.create(
			customer=self.customer,
			created_by=self.user,
		)

		SalesOrderItem.objects.bulk_create([
			SalesOrderItem(order=self.order, product=self.product, quantity=2)
		])
		self.order_item = SalesOrderItem.objects.get(order=self.order, product=self.product)

		self.packing_order = PackingOrder.objects.create(order=self.order)
		PackingOrderItem.objects.create(
			packing_order=self.packing_order,
			sales_order_item=self.order_item,
			product=self.product,
			quantity_required=2,
			quantity_scanned=0,
		)

	def test_complete_packing_returns_400_when_scans_incomplete(self):
		response = self.client.post(
			reverse('packing:complete_packing', args=[self.packing_order.id]),
			data={'items': [{'sku': 'LK-001', 'quantity_scanned': 1}]},
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('Cannot set PackingOrder to PACKED', response.json().get('error', ''))

		self.packing_order.refresh_from_db()
		self.assertEqual(self.packing_order.status, PackingOrder.PackingStatus.PENDING)

	def test_complete_packing_sets_status_to_packed_when_all_scanned(self):
		self.client.force_login(self.user)

		response = self.client.post(
			reverse('packing:complete_packing', args=[self.packing_order.id]),
			data={'items': [{'sku': 'LK-001', 'quantity_scanned': 2}]},
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json(), {'ok': True})

		self.packing_order.refresh_from_db()
		self.assertEqual(self.packing_order.status, PackingOrder.PackingStatus.PACKED)
		self.assertTrue(self.packing_order.stock_deducted)
		self.assertEqual(self.packing_order.packed_by, self.user)
		self.order.refresh_from_db()
		self.assertEqual(self.order.status, SalesOrder.SalesOrderStatus.PACKED)

		packing_item = self.packing_order.items_to_pack.get()
		self.assertEqual(packing_item.quantity_scanned, 2)

	def test_complete_packing_returns_400_when_item_product_missing(self):
		self.client.force_login(self.user)

		packing_item = self.packing_order.items_to_pack.get()
		packing_item.product = None
		packing_item.save(update_fields=['product'])

		response = self.client.post(
			reverse('packing:complete_packing', args=[self.packing_order.id]),
			data={'items': [{'sku': 'LK-001', 'quantity_scanned': 2}]},
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('deleted products', response.json().get('error', ''))

		self.packing_order.refresh_from_db()
		self.assertEqual(self.packing_order.status, PackingOrder.PackingStatus.PENDING)

	def test_ship_packing_sets_shipping_statuses_and_tracking(self):
		self.client.force_login(self.user)

		self.client.post(
			reverse('packing:complete_packing', args=[self.packing_order.id]),
			data={'items': [{'sku': 'LK-001', 'quantity_scanned': 2}]},
			content_type='application/json',
		)

		response = self.client.post(
			reverse('packing:ship_packing', args=[self.packing_order.id]),
			data={'carrier': Tracking.TrackingCarrier.DHL, 'tracking_number': 'TRK-001'},
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json(), {'ok': True})

		self.packing_order.refresh_from_db()
		self.order.refresh_from_db()
		self.assertEqual(self.packing_order.status, PackingOrder.PackingStatus.SHIPPED)
		self.assertEqual(self.order.status, SalesOrder.SalesOrderStatus.SHIPPED)
		self.assertIsNotNone(self.order.tracking_id)
		self.assertEqual(self.order.tracking.tracking_number, 'TRK-001')
		self.assertEqual(self.order.tracking.status, Tracking.TrackingStatus.SHIPPED)

	def test_deliver_packing_sets_delivered_statuses(self):
		self.client.force_login(self.user)

		self.client.post(
			reverse('packing:complete_packing', args=[self.packing_order.id]),
			data={'items': [{'sku': 'LK-001', 'quantity_scanned': 2}]},
			content_type='application/json',
		)
		self.client.post(
			reverse('packing:ship_packing', args=[self.packing_order.id]),
			data={'carrier': Tracking.TrackingCarrier.DHL, 'tracking_number': 'TRK-002'},
			content_type='application/json',
		)

		response = self.client.post(
			reverse('packing:deliver_packing', args=[self.packing_order.id]),
			data={},
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json(), {'ok': True})

		self.order.refresh_from_db()
		self.assertEqual(self.order.status, SalesOrder.SalesOrderStatus.DELIVERED)
		self.assertEqual(self.order.tracking.status, Tracking.TrackingStatus.DELIVERED)

	def test_ship_requires_packed_status(self):
		response = self.client.post(
			reverse('packing:ship_packing', args=[self.packing_order.id]),
			data={'carrier': Tracking.TrackingCarrier.DHL, 'tracking_number': 'TRK-003'},
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('Only PACKED orders can be shipped', response.json().get('error', ''))

	def test_deliver_requires_shipped_status(self):
		response = self.client.post(
			reverse('packing:deliver_packing', args=[self.packing_order.id]),
			data={},
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('Only SHIPPED orders can be delivered', response.json().get('error', ''))


class ReservationSplitBetweenAssignedAndMainTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username='seller',
			email='seller@example.com',
			password='testpass123',
		)

		self.assigned_warehouse = Warehouse.objects.create(
			name='Store Warehouse',
			address='Store 1',
			city='Berlin',
			state='BE',
			zip_code='10000',
			country='DE',
			warehouse_type=Warehouse.WarehouseType.SHOP,
			created_by=self.user,
		)

		self.main_warehouse = Warehouse.objects.create(
			name='Main Warehouse',
			address='Main 1',
			city='Berlin',
			state='BE',
			zip_code='10000',
			country='DE',
			warehouse_type=Warehouse.WarehouseType.MAIN,
			created_by=self.user,
		)

		UserProfile.objects.create(
			user=self.user,
			email='seller-profile@example.com',
			assigned_warehouse=self.assigned_warehouse,
		)

		self.assigned_product = Product.objects.create(
			name='Water',
			sku='WATER-001',
			price='1.99',
			reserved_quantity=0,
			stock_quantity=100,
			product_location=self.assigned_warehouse,
			created_by=self.user,
		)

		self.main_product = Product.objects.create(
			name='Water',
			sku='WATER-001',
			price='1.99',
			reserved_quantity=0,
			stock_quantity=200,
			product_location=self.main_warehouse,
			created_by=self.user,
		)

		self.customer = Customer.objects.create(
			first_name='Anna',
			last_name='Nowak',
			email='anna@example.com',
			created_by=self.user,
		)

	def test_second_order_is_split_between_assigned_and_main(self):
		first_order = SalesOrder.objects.create(customer=self.customer, created_by=self.user)
		first_item = SalesOrderItem.objects.create(
			order=first_order,
			product=self.assigned_product,
			quantity=90,
		)

		first_item.refresh_from_db()
		self.assigned_product.refresh_from_db()
		self.main_product.refresh_from_db()

		self.assertEqual(first_item.reserved_from_assigned, 90)
		self.assertEqual(first_item.reserved_from_main, 0)
		self.assertEqual(self.assigned_product.reserved_quantity, 90)
		self.assertEqual(self.main_product.reserved_quantity, 0)
		self.assertFalse(PackingOrder.objects.filter(order=first_order).exists())

		second_order = SalesOrder.objects.create(customer=self.customer, created_by=self.user)
		second_item = SalesOrderItem.objects.create(
			order=second_order,
			product=self.assigned_product,
			quantity=20,
		)

		second_item.refresh_from_db()
		self.assigned_product.refresh_from_db()
		self.main_product.refresh_from_db()

		self.assertEqual(second_item.reserved_from_assigned, 10)
		self.assertEqual(second_item.reserved_from_main, 10)
		self.assertEqual(self.assigned_product.reserved_quantity, 100)
		self.assertEqual(self.main_product.reserved_quantity, 10)

		packing_order = PackingOrder.objects.filter(order=second_order).first()
		self.assertIsNotNone(packing_order)
		packing_item = PackingOrderItem.objects.filter(
			packing_order=packing_order,
			sales_order_item=second_item,
		).first()
		self.assertIsNotNone(packing_item)
		self.assertEqual(packing_item.quantity_required, 10)
