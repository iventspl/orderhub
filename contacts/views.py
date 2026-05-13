from django.shortcuts import render

def contacts_list(request):
    return render(request, 'contacts/contacts_list.html', {'page': 'contacts'})
