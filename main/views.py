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
    form = BidForm()

    if request.method == "POST":
        form = BidForm(request.POST)

        if form.is_valid():
            amount = form.cleaned_data["amount"]

            if amount <= lot.current_price:
                messages.error(
                    request,
                    f"Ставка должна быть больше текущей цены ({lot.current_price} ₽)!",
                )
            elif request.user == lot.owner:
                messages.error(
                    request, "Вы не можете делать ставки на собственный лот!"
                )
            elif request.user.is_authentificated:
                with transaction.atomic():
                    bid = form.save(commit=False)
                    bid.lot = Lot
                    bid.bidder = request.user
                    bid.save()

                    lot.current_price = amount
                    lot.save(update_fields=["current_price"])

                messages.success(request, f"Ваша ставка {amount} ₽ успешно принята!")
                return redirect("lot_detail", lot_id=lot.id)
            else:
                messages.error(
                    request, "Чтобы делать ставки, вам нужно войти в аккаунт."
                )

    return render(request, "main/lot_detail.html", {"lot": lot, "form": form})
