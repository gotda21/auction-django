from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Lot, Bid
from .forms import BidForm, CustomUserCreationForm
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView


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

            if timezone.now() > lot.end_time:
                messages.error(
                    request, "Аукцион уже завершён! Ставки больше не принимаются."
                )
                return render(
                    request, "main/lot_detail.html", {"lot": lot, "form": form}
                )

            elif amount <= lot.current_price:
                messages.error(
                    request,
                    f"Ставка должна быть больше текущей цены ({lot.current_price} ₽)!",
                )
                return render(
                    request, "main/lot_detail.html", {"lot": lot, "form": form}
                )

            elif request.user == lot.owner:
                messages.error(
                    request, "Вы не можете делать ставки на собственный лот!"
                )
                return render(
                    request, "main/lot_detail.html", {"lot": lot, "form": form}
                )

            elif request.user.is_authenticated:
                with transaction.atomic():
                    bid = form.save(commit=False)
                    bid.lot = lot
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
    bids = lot.bids.all().order_by("-amount")

    return render(
        request, "main/lot_detail.html", {"lot": lot, "form": form, "bids": bids}
    )


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "main/register.html"
    success_url = reverse_lazy("login")
