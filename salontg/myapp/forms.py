from django import forms
from .models import Users, Appointments
from django.core.exceptions import ValidationError
import re

class RegisterForm(forms.ModelForm):
    password2 = forms.CharField(widget=forms.PasswordInput, label='Подтверждение пароля')
    
    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'phone', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^7\d{10}$', phone):
            raise ValidationError('Телефон должен быть в формате 7XXXXXXXXXX (11 цифр)')
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        
        if password and password2 and password != password2:
            self.add_error('password2', 'Пароли не совпадают')
        
        return cleaned_data

class LoginForm(forms.Form):
    phone = forms.CharField(label='Телефон', max_length=11)
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')

class BookingForm(forms.ModelForm):
    class Meta:
        model = Appointments
        fields = ['service', 'master', 'date', 'time', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }