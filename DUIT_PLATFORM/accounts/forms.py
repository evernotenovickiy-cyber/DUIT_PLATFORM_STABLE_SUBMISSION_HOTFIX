from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from listings.catalog_data import RUSSIA_CITIES
from .models import Profile

User = get_user_model()


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Email или логин", widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "name@example.com"}))
    password = forms.CharField(label="Пароль", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "placeholder": "Ваш пароль"}))

    def clean(self):
        identifier = self.cleaned_data.get("username")
        if identifier and "@" in identifier:
            user = User.objects.filter(email__iexact=identifier.strip()).first()
            if user:
                self.cleaned_data["username"] = user.get_username()
        return super().clean()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True, label="Имя", max_length=80)
    last_name = forms.CharField(required=False, label="Фамилия", max_length=80)
    email = forms.EmailField(required=True, label="Email")
    role = forms.ChoiceField(required=True, label="Как вы хотите пользоваться DUIT?", choices=Profile.Role.choices, widget=forms.RadioSelect)
    city = forms.ChoiceField(required=False, label="Город", choices=[("", "Выберите город")] + [(city, city) for city in RUSSIA_CITIES])

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "role", "city", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Логин"
        self.fields["username"].help_text = "Короткое уникальное имя для ссылки на профиль. Например: anna_cakes"
        self.fields["password1"].label = "Пароль"
        self.fields["password2"].label = "Повторите пароль"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data.get("last_name", "").strip()
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data["role"]
            profile.city = self.cleaned_data.get("city", "")
            profile.save(update_fields=["role", "city"])
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["role", "avatar", "headline", "bio", "city", "phone", "telegram"]
        widgets = {
            "role": forms.Select(),
            "headline": forms.TextInput(attrs={"placeholder": "Например: Кондитер · авторские торты"}),
            "bio": forms.Textarea(attrs={"rows": 5, "placeholder": "Расскажите о себе, опыте и подходе к работе"}),
            "city": forms.TextInput(attrs={"placeholder": "Москва"}),
            "phone": forms.TextInput(attrs={"placeholder": "+7 900 000-00-00"}),
            "telegram": forms.TextInput(attrs={"placeholder": "@username"}),
        }
