from django.shortcuts import render
from .models import Customer
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.contrib import messages
from users.models import Membership

@login_required
def customers_list(request):
    user_company = get_object_or_404(Membership, user=request.user)
    customers = Customer.objects.filter(company_id=user_company.company_id).order_by('-created_on')
    context = {
        'customers': customers,
        'page': 'customers',
    }
    return render(request, 'customers/customers_list.html', context)
