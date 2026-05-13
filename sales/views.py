from django.shortcuts import render

def sales_list(request):
    return render(request, 'sales/sales_list.html', {'page': 'sales'})