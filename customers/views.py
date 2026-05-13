from django.shortcuts import render

def customers_list(request):
    return render(request, 'customers/customers_list.html', {'page': 'customers'})
