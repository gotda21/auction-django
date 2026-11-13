from django.shortcuts import render
from .models import Lot

def lot_list(request):
    lots = Lot.objects.all()
    return render(request, 'main/lot_list.html', {'lots': lots})