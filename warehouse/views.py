from django.shortcuts import render

def warehouse_list(request):
    return render(request, 'warehouse/warehouse_list.html', {'page': 'warehouse'})
