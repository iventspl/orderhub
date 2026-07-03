from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@login_required
def contacts_list(request):
    return render(request, 'contacts/contacts_list.html', {'page': 'contacts'})
