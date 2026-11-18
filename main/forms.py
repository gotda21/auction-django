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
                    "class": "form-control form-control-lg",
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
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "start_price": forms.NumberInput(attrs={"class": "form-control"}),
            "min_bid_step": forms.NumberInput(attrs={"class": "from-control"}),
            "condition": forms.Select(attrs={"class": "form-select"}),
            "end_time": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }
