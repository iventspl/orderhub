from django.shortcuts import render

def transfers_list(request):
    return render(request, 'transfers/transfers_list.html', {'page': 'transfers'})
