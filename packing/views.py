from django.shortcuts import render

def packing_list(request):
    return render(request, 'packing/packing_list.html', {'page': 'packing'})
