from django import forms
from .models import Bid

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Введите вашу ставку...',
                'step': '0.01'
            })
        }
        labels = {
            'amount': 'Сумма ставки (₽)'
        }