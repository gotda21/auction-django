from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Lot, Bid, Category
from .forms import BidForm, CustomUserCreationForm, LotForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.db.models import Q


def lot_list(request):
    lots = Lot.objects.all()
    search_query = request.GET.get("search", "")
    category_id = request.GET.get("category", "")

    if search_query:
        lots = lots.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
    if category_id:
        lots = lots.filter(category_id=category_id)

    categories = Category.objects.all()

    context = {
        "lots": lots,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category_id,
    }

    if request.META.get("HTTP_HX_REQUEST"):
        return render(request, "main/_lot_cards.html", context)

    return render(request, "main/lot_list.html", context)


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


@login_required
def profile(request):
    won_lots = Lot.objects.filter(winner=request.user)
    my_bids = request.user.bids.all().select_related("lot").order_by("-created_at")
    my_lots = request.user.owner_lots.all()

    context = {
        "won_lots": won_lots,
        "my_bids": my_bids,
        "my_lots": my_lots,
    }

    return render(request, "main/profile.html", context)


@login_required
def lot_create(request):
    if request.method == "POST":
        form = LotForm(request.POST)
        if form.is_valid():
            lot = form.save(commit=False)
            lot.owner = request.user
            lot.current_price = lot.start_price
            lot.save()
            messages.success(
                request, "Лот успешно создан! Теперь вы можете загрузить фотографии."
            )
            return redirect("lot_detail", lot_id=lot.id)
    else:
        form = LotForm()

    return render(request, "main/lot_form.html", {"form": form})
