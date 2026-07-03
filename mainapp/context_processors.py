from customers.models import Customer
from sales.models import SalesOrder
from inventory.models import Product
from warehouse.models import Warehouse
from transfers.models import Transfer
# from reports.models import Report
# from contacts.models import Contact
from packing.models import PackingOrder
from tracking.models import Tracking
from users.models import Membership, UserProfile


def _empty_stats():
    return {
        'total_sales_orders': 0,
        'total_customers': 0,
        'total_products': 0,
        'total_warehouses': 0,
        'total_transfers': 0,
        'total_packing_orders': 0,
        'total_tracking': 0,
        'total_reports': 0,
        'total_contacts': 0,
        'total_staff':0
    }


def global_stats(request):
    user = request.user
    if not user.is_authenticated:
        return _empty_stats()

    membership = Membership.objects.select_related('company').filter(user=user).first()
    if membership is None:
        return _empty_stats()

    user_company = membership.company
    return {
        'total_sales_orders': SalesOrder.objects.filter(company_id=user_company.id).count(),
        'total_customers': Customer.objects.filter(company_id=user_company.id).count(),
        'total_products': Product.objects.filter(company_id=user_company.id).count(),
        'total_warehouses': Warehouse.objects.filter(company_id=user_company.id).count(),
        'total_transfers': Transfer.objects.filter(company_id=user_company.id).count(),
        # 'total_reports': Report.objects.filter(company_id=user_company.id).count(),
        # 'total_contacts': Contact.objects.filter(company_id=user_company.id).count(),
        'total_packing_orders': PackingOrder.objects.filter(company_id=user_company.id).count(),
        'total_tracking': Tracking.objects.filter(company_id=user_company.id).count(),
        'total_staff': UserProfile.objects.filter(active_company=user_company.id).count(),
    }