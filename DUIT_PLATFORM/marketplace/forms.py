from django import forms
from django.utils import timezone

from .models import Message, Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["desired_date", "desired_time", "note"]
        widgets = {
            "desired_date": forms.DateInput(attrs={"type": "date"}),
            "desired_time": forms.TimeInput(attrs={"type": "time"}),
            "note": forms.Textarea(attrs={"rows": 4, "placeholder": "Опишите задачу, адрес или другие пожелания..."})
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 2, "placeholder": "Напишите сообщение...", "maxlength": 3000})
        }


class PaymentForm(forms.Form):
    method = forms.ChoiceField(
        label="Способ оплаты",
        choices=(("card", "Банковская карта"), ("after_service", "После выполнения")),
        widget=forms.RadioSelect,
        initial="card",
    )
    card_holder = forms.CharField(label="Имя на карте", required=False, max_length=80, widget=forms.TextInput(attrs={"autocomplete": "cc-name", "placeholder": "IVAN IVANOV"}))
    card_number = forms.CharField(label="Номер карты", required=False, max_length=19, widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "cc-number", "placeholder": "4242 4242 4242 4242"}))
    expiry = forms.CharField(label="Срок", required=False, max_length=5, widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "cc-exp", "placeholder": "12/30"}))
    cvv = forms.CharField(label="CVV", required=False, max_length=3, widget=forms.PasswordInput(attrs={"inputmode": "numeric", "autocomplete": "cc-csc", "placeholder": "123"}))

    SUCCESS_CARD = "4242424242424242"
    DECLINED_CARD = "4000000000000002"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("method") != "card":
            return cleaned
        number = "".join(ch for ch in cleaned.get("card_number", "") if ch.isdigit())
        cleaned["card_number"] = number
        if number not in {self.SUCCESS_CARD, self.DECLINED_CARD}:
            self.add_error("card_number", "Используйте тестовую карту DUIT: 4242 4242 4242 4242.")
        if not cleaned.get("card_holder", "").strip():
            self.add_error("card_holder", "Укажите имя на карте.")
        expiry = cleaned.get("expiry", "").strip()
        if len(expiry) != 5 or expiry[2:3] != "/" or not (expiry[:2] + expiry[3:]).isdigit():
            self.add_error("expiry", "Формат срока: MM/YY.")
        else:
            month = int(expiry[:2])
            year = 2000 + int(expiry[3:])
            now = timezone.localdate()
            if month < 1 or month > 12:
                self.add_error("expiry", "Укажите корректный месяц от 01 до 12.")
            elif (year, month) < (now.year, now.month):
                self.add_error("expiry", "Срок действия тестовой карты уже истёк.")
        cvv = cleaned.get("cvv", "").strip()
        if len(cvv) != 3 or not cvv.isdigit():
            self.add_error("cvv", "CVV — 3 цифры.")
        return cleaned
