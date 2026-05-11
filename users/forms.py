from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Client


class ClientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Имя")
    last_name = forms.CharField(max_length=30, required=True, label="Фамилия")
    patronymic = forms.CharField(max_length=100, required=False, label="Отчество")
    phone = forms.CharField(max_length=20, required=True, label="Телефон (формат: +375 (29) XXX-XX-XX)")
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True, label="Дата рождения")
    client_type = forms.ChoiceField(choices=Client.ClientType.choices, label="Тип клиента")
    company_name = forms.CharField(max_length=150, required=False, label="Название компании (для юр. лиц)")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        client_type = cleaned_data.get('client_type')
        company_name = cleaned_data.get('company_name')

        if client_type == Client.ClientType.LEGAL and not company_name:
            self.add_error('company_name', "Company name is required for legal entities.")

        if client_type == Client.ClientType.INDIVIDUAL and company_name:
            self.add_error('company_name', "Company name must be empty for private individuals.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            Client.objects.create(
                user=user,
                patronymic=self.cleaned_data.get('patronymic'),
                phone=self.cleaned_data.get('phone'),
                birth_date=self.cleaned_data.get('birth_date'),
                client_type=self.cleaned_data.get('client_type'),
                company_name=self.cleaned_data.get('company_name')
            )
        return user
