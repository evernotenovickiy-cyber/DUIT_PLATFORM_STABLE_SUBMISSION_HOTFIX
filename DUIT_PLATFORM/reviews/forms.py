from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "text"]
        widgets = {
            "rating": forms.RadioSelect,
            "text": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Как прошла работа с исполнителем?"}
            ),
        }
