from django.db.models import Q, Sum, F
from rest_framework.decorators import api_view
from rest_framework.response import Response
from sales.models import SalesOrder
from users.models import Membership, UserProfile
from warehouse.models import Warehouse
from .serializers import SalesOrderSerializer
from inventory.models import Product


@api_view(['GET'])
def api_get_sales_orders(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=401)

    user_company = Membership.objects.filter(user=request.user).first()
    if not user_company:
        return Response({'error': 'User does not belong to any company'}, status=403)
    sales_orders = (
        SalesOrder.objects
        .filter(company_id=user_company.company_id)
        .select_related('customer', 'tracking')
        .prefetch_related('salesorderitem_set')
        .order_by('-created_on')
    )

    serializer = SalesOrderSerializer(sales_orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_search_products(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=401)

    query = request.GET.get('q', '').strip()
    if not query:
        return Response({'error': 'Query parameter "q" is required'}, status=400)

    membership = Membership.objects.filter(user=request.user).first()
    if not membership:
        return Response({'error': 'User does not belong to any company'}, status=403)

    company_id = membership.company_id

    profile = UserProfile.objects.select_related('assigned_warehouse').filter(user=request.user).first()
    assigned_warehouse = profile.assigned_warehouse if profile else None

    main_warehouse = Warehouse.objects.filter(
        warehouse_type=Warehouse.WarehouseType.MAIN,
        company_id=company_id,
    ).first()

    valid_ids = [w.id for w in (assigned_warehouse, main_warehouse) if w is not None]

    # Prefer MAIN rows so that when we deduplicate by SKU the MAIN product is returned.
    # The order signal uses product.sku to locate stock, so the returned ID just needs
    # to belong to a valid product row for that SKU.
    qs = (
        Product.objects
        .filter(
            company_id=company_id,
            product_location_id__in=valid_ids,
        )
        .filter(Q(name__icontains=query) | Q(sku__icontains=query))
        .select_related('product_location')
        .order_by(
            # MAIN rows first so they win deduplication
            F('product_location__warehouse_type').asc(),  # MAIN < SHOP alphabetically
            'name',
        )
    )

    seen_skus = set()
    results = []
    for product in qs:
        if product.sku in seen_skus:
            continue
        seen_skus.add(product.sku)

        # Total available stock for this SKU across valid warehouses
        agg = Product.objects.filter(
            sku=product.sku,
            company_id=company_id,
            product_location_id__in=valid_ids,
        ).aggregate(available=Sum(F('stock_quantity') - F('reserved_quantity')))
        available = max(agg['available'] or 0, 0)

        results.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'get_total_quantity': available,
        })
        if len(results) >= 10:
            break

    return Response(results)