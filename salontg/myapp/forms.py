from django import forms
from django.core.validators import RegexValidator, EmailValidator
from django.contrib.auth.hashers import make_password
from .models import Users, Services, Masters, Appointments, Photo

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        }),
        label='Пароль',
        min_length=6,
        help_text='Минимум 6 символов'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        }),
        label='Подтверждение пароля'
    )
    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+79991234567'
        }),
        label='Телефон'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        }),
        label='Email'
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иван'
        }),
        label='Имя'
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иванов'
        }),
        label='Фамилия'
    )
    
    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'phone', 'email', 'password']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Users.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        # Нормализуем номер: убираем всё кроме цифр
        cleaned_phone = ''.join(c for c in phone if c.isdigit())
        
        # Форматируем в +7ХХХХХХХХХХ
        if len(cleaned_phone) == 11 and cleaned_phone.startswith('7'):
            phone = '+' + cleaned_phone
        elif len(cleaned_phone) == 10:
            phone = '+7' + cleaned_phone
        elif len(cleaned_phone) == 11 and cleaned_phone.startswith('8'):
            phone = '+7' + cleaned_phone[1:]
        
        # Проверяем уникальность
        if Users.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Пользователь с таким телефоном уже существует")
        
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        
        if password and password2 and password != password2:
            self.add_error('password2', "Пароли не совпадают")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])
        user.role = 'client'
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваш логин'
        }),
        label='Логин'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль',
            'autocomplete': 'current-password'
        }),
        label='Пароль'
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not Users.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином не найден")
        return username


class BookingForm(forms.Form):
    client_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иван Иванов'
        }),
        label='Ваше имя',
        required=True
    )
    client_phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+79991234567'
        }),
        label='Телефон',
        validators=[
            RegexValidator(
                regex=r'^\+?7\d{10}$',
                message="Номер телефона должен быть в формате: +79991234567"
            )
        ],
        required=True
    )
    client_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        }),
        label='Email',
        required=False
    )
    service = forms.ModelChoiceField(
        queryset=Services.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Услуга',
        required=True
    )
    master = forms.ModelChoiceField(
        queryset=Masters.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Мастер',
        required=True
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Дата',
        required=True
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label='Время',
        required=True
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Дополнительные пожелания (необязательно)'
        }),
        label='Примечания',
        required=False
    )
    
    def clean(self):
        cleaned_data = super().clean()
        master = cleaned_data.get('master')
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        
        if master and date and time:
            # Проверяем, занято ли время
            is_time_available = not Appointments.objects.filter(
                master=master,
                date=date,
                time=time,
                status__in=['confirmed', 'pending']
            ).exists()
            
            if not is_time_available:
                raise forms.ValidationError("Выбранное время уже занято. Пожалуйста, выберите другое время.")
        
        return cleaned_data

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['title', 'image', 'description']