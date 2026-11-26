from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Lot, Bid, Category, LotImage, Notification
from .forms import BidForm, CustomUserCreationForm, LotForm, UserProfileForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
import re


def lot_list(request):
    lots = Lot.objects.all()
    search_query = request.GET.get("search", "").strip()
    category_id = request.GET.get("category", "")
    condition = request.GET.get("condition", "")
    price_min = request.GET.get("price_min", "")
    price_max = request.GET.get("price_max", "")
    sort_by = request.GET.get("sort", "")

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

    paginator = Paginator(lots, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        "lots": page_obj,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category_id,
        "page_obj": page_obj,
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
def profile(request, username=None):
    if username:
        user_profile = get_object_or_404(get_user_model(), username=username)
    else:
        user_profile = request.user

    if request.user == user_profile and request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлён!")
            return redirect("profile")
    else:
        form = (
            UserProfileForm(instance=user_profile)
            if request.user == user_profile
            else None
        )

    won_lots = Lot.objects.filter(winner=user_profile)
    my_lots = user_profile.owner_lots.all()
    my_bids = None

    if request.user == user_profile:
        my_bids = request.user.bids.all().select_related("lot").order_by("-created_at")

    context = {
        "user_profile": user_profile,
        "won_lots": won_lots,
        "my_bids": my_bids,
        "my_lots": my_lots,
        "is_own_profile": request.user == user_profile,
        "form": form,
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
            main_index = int(request.POST.get("main_new_image_index", 0))

            for i, image in enumerate(images):
                LotImage.objects.create(lot=lot, image=image, is_main=(i == main_index))

            messages.success(request, "Лот успешно создан!")
            return redirect("lot_detail", lot_id=lot.id)
    else:
        form = LotForm()

    return render(request, "main/lot_form.html", {"form": form})


@login_required
def lot_edit(request, lot_id):
    lot = get_object_or_404(Lot, pk=lot_id)

    if request.user != lot.owner:
        messages.error(request, "У вас нет прав на редактирование этого лота.")
        return redirect("lot_detail", lot_id=lot.id)

    # --- 1. ОБРАБОТКА AJAX ДЛЯ СТАРЫХ ФОТО (БЕЗ ПЕРЕЗАГРУЗКИ) ---
    if request.method == "POST" and request.POST.get("action") == "set_main_existing":
        image_id = request.POST.get("image_id")
        image = get_object_or_404(LotImage, id=image_id, lot=lot)

        # Снимаем галочки со всех
        LotImage.objects.filter(lot=lot).update(is_main=False)
        # Ставим на выбранное
        image.is_main = True
        image.save()

        return JsonResponse({"status": "ok"})

    # --- 2. ОБРАБОТКА СОХРАНЕНИЯ ФОРМЫ (НОВЫЕ ФОТО) ---
    if request.method == "POST":
        form = LotForm(request.POST, instance=lot)
        if form.is_valid():
            form.save()

            new_main_index_str = request.POST.get("main_new_image_index")

            # Проверяем, выбрал ли пользователь главное среди НОВЫХ фото
            # (Если он не нажимал на кнопку "Сделать главным" у новых, там по умолчанию 0)
            # Но чтобы не сбивать старое главное, мы проверяем, есть ли вообще новые файлы
            images = request.FILES.getlist("images")

            if images:
                new_main_index = int(new_main_index_str) if new_main_index_str else 0
                # Снимаем галочки со старых, так как пользователь загрузил новые и выбрал среди них
                LotImage.objects.filter(lot=lot).update(is_main=False)

                for i, image in enumerate(images):
                    LotImage.objects.create(
                        lot=lot, image=image, is_main=(i == new_main_index)
                    )

            messages.success(request, "Лот успешно обновлен!")
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


@login_required
def lot_image_delete(request, image_id):
    image = get_object_or_404(LotImage, id=image_id)

    if request.user != image.lot.owner:
        messages.error(request, "У вас нет прав на удаление этого фото.")
        return redirect("lot_detail", lot_id=image.lot.id)

    lot_id = image.lot.id
    was_main = image.is_main  # Запоминаем, было ли оно главным
    image.delete()

    # Если удалили главное, назначаем новое главное (первое из оставшихся)
    if was_main:
        next_image = LotImage.objects.filter(lot_id=lot_id).first()
        if next_image:
            next_image.is_main = True
            next_image.save()

    messages.success(request, "Фотография удалена.")
    return redirect("lot_edit", lot_id=lot_id)


@login_required
def lot_delete(request, lot_id):
    lot = get_object_or_404(Lot, pk=lot_id)

    if request.user != lot.owner:
        messages.error(request, "У вас нет прав на удаление данного лота.")
        return redirect("lot_detail", lot_id=lot.id)

    if request.method == "POST":
        lot.delete()
        messages.success(request, "Лот успешно удален!")
        return redirect("profile")

    return render(request, "main/lot_confirm_delete.html", {"lot": lot})
