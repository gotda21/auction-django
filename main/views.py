from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Lot, Bid, Category, LotImage, Notification
from .forms import BidForm, CustomUserCreationForm, LotForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.db.models import Q
import re


def lot_list(request):
    lots = Lot.objects.all()
    search_query = request.GET.get("search", "").strip()
    category_id = request.GET.get("category", "")

    if search_query:
        query_words = re.split(r"\s+", search_query)
        query_conditions = Q()
        for word in query_words:
            if word:
                query_conditions |= Q(title__icontains=word) | Q(
                    description__icontains=word
                )
        lots = lots.filter(query_conditions)
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
                    previous_bid = lot.bids.order_by("-amount").first()
                    bid = form.save(commit=False)
                    bid.lot = lot
                    bid.bidder = request.user
                    bid.save()

                    lot.current_price = amount
                    lot.save(update_fields=["current_price"])

                    if previous_bid and previous_bid.bidder != request.user:
                        Notification.objects.create(
                            user=previous_bid.bidder,
                            notification_type=Notification.Type.OUTBID,
                            lot=lot,
                            message=f"Ваша ставка на лот '{lot.title}' была перебита. Новая ставка: '{amount}' ₽",
                        )

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

            images = request.FILES.getlist("images")
            for i, image in enumerate(images):
                LotImage.objects.create(lot=lot, image=image, is_main=(i == 0))

            messages.success(
                request, "Лот успешно создан! Теперь вы можете загрузить фотографии."
            )
            return redirect("lot_detail", lot_id=lot.id)
    else:
        form = LotForm()

    return render(request, "main/lot_form.html", {"form": form})


@login_required
def lot_edit(request, lot_id):
    lot = get_object_or_404(Lot, pk=lot_id)

    if request.user != lot.owner:
        messages.error(request, "У вас нет прав на редактирование этого лота.")

    if request.method == "POST":
        form = LotForm(request.POST, instance=lot)
        if form.is_valid():
            form.save()

            images = request.FILES.getlist("images")
            for image in images:
                LotImage.objects.create(lot=lot, image=image, is_main=False)

            messages.success(request, "Лот успешно обновлён!")
            return redirect("lot_detail", lot_id=lot.id)
    else:
        form = LotForm(instance=lot)

    return render(request, "main/lot_form.html", {"form": form, "is_edit": True})


@login_required
def notifications(request):
    user_notifications = request.user.notifications.all().order_by("-created_at")
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(
        request, "main/notifications.html", {"notifications": user_notifications}
    )
