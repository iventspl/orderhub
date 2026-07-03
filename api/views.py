from rest_framework.decorators import api_view
from rest_framework.response import Response
from sales.models import SalesOrder
from users.models import Membership
from .serializers import SalesOrderSerializer
from inventory.models import Product

@api_view(['GET'])
def api_get_sales_orders(request):
    """API endpoint to retrieve sales orders for the authenticated user's company."""
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
    """API endpoint to search for products based on a query parameter."""
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=401)

    query = request.GET.get('q', '')
    if not query:
        return Response({'error': 'Query parameter "q" is required'}, status=400)

    user_company = Membership.objects.filter(user=request.user).first()
    if not user_company:
        return Response({'error': 'User does not belong to any company'}, status=403)

    products = (
        Product.objects
        .filter(company_id=user_company.company_id, name__icontains=query).distinct('name')
        .order_by('name')[:10]  # Limit to 10 results for performance
    )

    return Response([{'id': product.id, 'name': product.name, 'sku': product.sku, 'get_total_quantity': product.get_total_quantity()} for product in products])