from django import forms

from .catalog_data import CATEGORY_GROUPS
from .models import Category, Service


class ServiceForm(forms.ModelForm):
    category_group = forms.ChoiceField(label="Сфера", required=False)
    class Meta:
        model = Service
        fields = ["title", "category", "description", "price", "pricing_type", "city", "service_format", "duration_minutes", "lead_time", "included", "process", "availability_note", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например: Маникюр с покрытием"}),
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Что входит в услугу, сроки, формат работы и важные детали...",
                }
            ),
            "price": forms.NumberInput(attrs={"placeholder": "0", "min": 0, "step": "1"}),
            "city": forms.TextInput(attrs={"placeholder": "Москва"}),
            "duration_minutes": forms.NumberInput(attrs={"min": 15, "step": 15, "placeholder": "60"}),
            "lead_time": forms.TextInput(attrs={"placeholder": "Например: сегодня после 18:00"}),
            "included": forms.Textarea(attrs={"rows": 4, "placeholder": "Что входит в стоимость: материалы, выезд, консультация..."}),
            "process": forms.Textarea(attrs={"rows": 4, "placeholder": "Опишите этапы: заявка → согласование → работа → результат"}),
            "availability_note": forms.TextInput(attrs={"placeholder": "Например: свободно сегодня и в выходные"}),
        }
        labels = {"is_active": "Опубликовать сразу"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category_group"].choices = [(g["slug"], f"{g['icon']} {g['title']}") for g in CATEGORY_GROUPS]

        selected_group = ""
        if self.is_bound:
            selected_group = self.data.get("category_group", "")
        elif self.instance and self.instance.pk and self.instance.category:
            for group in CATEGORY_GROUPS:
                if any(name == self.instance.category.name for name, _ in group["items"]):
                    selected_group = group["slug"]
                    break
        if not selected_group and CATEGORY_GROUPS:
            selected_group = CATEGORY_GROUPS[0]["slug"]
        self.fields["category_group"].initial = selected_group

        allowed_names = []
        for group in CATEGORY_GROUPS:
            if group["slug"] == selected_group:
                allowed_names = [name for name, _ in group["items"]]
                break
        self.fields["category"].queryset = Category.objects.all().order_by("name")
        self.fields["category"].empty_label = "Выберите направление"

        for name in ("pricing_type", "service_format", "duration_minutes"):
            self.fields[name].required = False

    def clean_category(self):
        category = self.cleaned_data.get("category")
        group_slug = self.cleaned_data.get("category_group")
        if category and group_slug:
            allowed = next(([name for name, _ in g["items"]] for g in CATEGORY_GROUPS if g["slug"] == group_slug), [])
            if category.name not in allowed:
                raise forms.ValidationError("Выберите направление из указанной сферы.")
        return category

    def clean_pricing_type(self):
        return self.cleaned_data.get("pricing_type") or "from"

    def clean_service_format(self):
        return self.cleaned_data.get("service_format") or "flexible"

    def clean_duration_minutes(self):
        return self.cleaned_data.get("duration_minutes") or 60

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("Цена не может быть отрицательной.")
        return price


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_clean(item, initial) for item in data]
        elif data:
            result = [single_clean(data, initial)]
        else:
            result = []

        for image in result:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Каждая фотография должна быть не больше 5 МБ.")
        return result


class ServicePhotosForm(forms.Form):
    photos = MultipleImageField(
        required=False,
        widget=MultipleImageInput(attrs={"accept": "image/*"}),
        label="Фотографии работ (до 6 штук)",
    )
