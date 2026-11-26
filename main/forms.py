from django import forms
from .models import Bid, User, Lot
from django.contrib.auth.forms import UserCreationForm


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ["amount"]
        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg border rounded-0",
                    "placeholder": "Введите вашу ставку...",
                    "step": "0.01",
                }
            )
        }
        labels = {"amount": "Сумма ставки (₽)"}


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class LotForm(forms.ModelForm):
    class Meta:
        model = Lot
        fields = [
            "title",
            "description",
            "category",
            "start_price",
            "min_bid_step",
            "condition",
            "end_time",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control rounded-0",
                    "placeholder": 'Например: Картина "Закат"',
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control rounded-0",
                    "rows": 4,
                    "placeholder": "Опишите состояние товара, его историю и т.д.",
                }
            ),
            "category": forms.Select(attrs={"class": "form-select rounded-0"}),
            "start_price": forms.NumberInput(attrs={"class": "form-control rounded-0"}),
            "min_bid_step": forms.NumberInput(
                attrs={"class": "form-control rounded-0"}
            ),
            "condition": forms.Select(attrs={"class": "form-select rounded-0"}),
            "end_time": forms.DateTimeInput(
                attrs={"class": "form-control rounded-0", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }
        labels = {
            "title": "Название лота",
            "description": "Описание",
            "category": "Категория",
            "start_price": "Стартовая цена (₽)",
            "min_bid_step": "Минимальный шаг ставки (₽)",
            "condition": "Состояние товара",
            "end_time": "Дата и время окончания",
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "avatar"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control rounded-0"}),
            "email": forms.EmailInput(attrs={"class": "form-control rounded-0"}),
            "avatar": forms.FileInput(attrs={"class": "form-control rounded-0"}),
        }
