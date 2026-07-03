from .models import Product
from .forms import AddProductForm
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from users.models import Membership, UserProfile

@login_required
def inventory_list(request):
    user_company = get_object_or_404(Membership, user=request.user).company
    profile = UserProfile.objects.select_related('assigned_warehouse').filter(user=request.user).first()
    assigned_warehouse = profile.assigned_warehouse if profile else None
    products = Product.objects.filter(company_id=user_company.id, product_location=assigned_warehouse).order_by('name', 'sku') if assigned_warehouse else Product.objects.filter(company_id=user_company.id).order_by('name', 'sku')

    context = {
        'page': 'inventory',
        'form': AddProductForm(company_id=user_company.id),
        'products': products,
    }
    return render(request, 'inventory/inventory_list.html', context)



@login_required
@require_POST
def add_product(request):
    user_company = get_object_or_404(Membership, user=request.user).company
    form = AddProductForm(request.POST, company_id=user_company.id)

    if form.is_valid():
        cleaned = form.cleaned_data
        profile = UserProfile.objects.select_related('assigned_warehouse').filter(user=request.user).first()
        default_location = profile.assigned_warehouse if profile else None
        product_location = cleaned['product_location'] or default_location

        if not product_location:
            messages.error(request, 'No warehouse selected and no assigned warehouse found for your profile.')
            return redirect('inventory:inventory_list')

        product = Product.objects.create(
            sku=cleaned['product_sku'],
            name=cleaned['product_name'],
            category=cleaned['product_category'],
            description=cleaned.get('product_description'),
            stock_quantity=cleaned['stock_quantity'],
            price=cleaned['price'],
            product_location=product_location,
            created_by=request.user,
            company = user_company,
        )
        messages.success(request, f'Added {product.stock_quantity} of {product.name} to inventory.')
    else:
        messages.error(request, 'Failed to add Product. Please correct the errors below.')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect('inventory:inventory_list')

