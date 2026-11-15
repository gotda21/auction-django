from django.shortcuts import render, get_object_or_404
from .models import Lot


def lot_list(request):
    lots = Lot.objects.all()
    return render(request, "main/lot_list.html", {"lots": lots})


def lot_detail(request, lot_id):
    lot = get_object_or_404(Lot, pk=lot_id)
    return render(request, "main/lot_detail.html", {"lot": lot})
