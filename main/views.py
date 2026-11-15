from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from .models import Lot, Bid
from .forms import BidForm


def lot_list(request):
    lots = Lot.objects.all()
    return render(request, "main/lot_list.html", {"lots": lots})


def lot_detail(request, lot_id):
    lot = get_object_or_404(Lot, pk=lot_id)
    return render(request, "main/lot_detail.html", {"lot": lot})
