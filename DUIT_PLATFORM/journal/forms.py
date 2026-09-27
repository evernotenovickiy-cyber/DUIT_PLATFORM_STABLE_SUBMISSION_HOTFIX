from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["kind", "city", "title", "excerpt", "body", "image_url"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например: Как выбрать мастера по ремонту"}),
            "excerpt": forms.Textarea(attrs={"rows": 2, "placeholder": "Коротко — о чём материал"}),
            "body": forms.Textarea(attrs={"rows": 10, "placeholder": "Полезный текст, история или локальная рекомендация"}),
            "city": forms.TextInput(attrs={"placeholder": "Москва"}),
            "image_url": forms.URLInput(attrs={"placeholder": "https://... (необязательно)"}),
        }
