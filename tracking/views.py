from django.shortcuts import render

def tracking_list(request):
    return render(request, 'tracking/tracking_list.html', {'page': 'tracking'})
