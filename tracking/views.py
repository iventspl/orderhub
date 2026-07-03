from django.shortcuts import render
from .models import Tracking
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from users.models import Membership


@login_required
def tracking_list(request):
    user_company = get_object_or_404(Membership, user=request.user).company

    context = {
        'page': 'tracking',
        'trackings': Tracking.objects.filter(company_id=user_company.id),
    }
    return render(request, 'tracking/tracking_list.html', context)
