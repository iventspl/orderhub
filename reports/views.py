from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@login_required
def reports_list(request):
    return render(request, 'reports/reports_list.html', {'page': 'reports'})
