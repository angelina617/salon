from django import forms
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password
from .models import Users, Services, Masters, Appointments, Photo

# ==================== ФОРМЫ ПОЛЬЗОВАТЕЛЕЙ ====================

class RegisterForm(forms.ModelForm):
    """Форма регистрации обычного пользователя (клиента)"""
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
        cleaned_phone = ''.join(c for c in phone if c.isdigit())
        
        if len(cleaned_phone) == 11 and cleaned_phone.startswith('7'):
            phone = '+' + cleaned_phone
        elif len(cleaned_phone) == 10:
            phone = '+7' + cleaned_phone
        elif len(cleaned_phone) == 11 and cleaned_phone.startswith('8'):
            phone = '+7' + cleaned_phone[1:]
        
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


class UserEditForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""
    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+79991234567',
            'readonly': 'readonly'
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
        fields = ['first_name', 'last_name', 'phone', 'email']
    
    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Users.objects.filter(email=email).exclude(id=self.user_instance.id).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email


class ChangePasswordForm(forms.Form):
    """Форма изменения пароля"""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Текущий пароль'
        }),
        label='Текущий пароль'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Новый пароль'
        }),
        label='Новый пароль',
        min_length=6
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите новый пароль'
        }),
        label='Подтверждение нового пароля'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password and new_password2 and new_password != new_password2:
            self.add_error('new_password2', "Пароли не совпадают")
        
        return cleaned_data


# ==================== ФОРМЫ МАСТЕРОВ ====================

class MasterRegisterForm(forms.ModelForm):
    """Форма регистрации мастера (создаёт пользователя + профиль мастера)"""
    # Поля пользователя
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
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        }),
        label='Пароль',
        min_length=6
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        }),
        label='Подтверждение пароля'
    )
    
    # Поля мастера
    specialization = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Стрижки, окрашивание'
        }),
        label='Специализация'
    )
    experience = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '5'
        }),
        label='Стаж (лет)',
        min_value=0
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Расскажите о себе и вашем опыте...'
        }),
        label='Описание'
    )
    photo = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        label='Фотография',
        required=False
    )
    
    class Meta:
        model = Masters
        fields = ['specialization', 'experience', 'description', 'photo']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Users.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        cleaned_phone = ''.join(c for c in phone if c.isdigit())
        
        if len(cleaned_phone) == 11 and cleaned_phone.startswith('7'):
            phone = '+' + cleaned_phone
        elif len(cleaned_phone) == 10:
            phone = '+7' + cleaned_phone
        elif len(cleaned_phone) == 11 and cleaned_phone.startswith('8'):
            phone = '+7' + cleaned_phone[1:]
        
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
        # Сначала создаём пользователя
        user = Users.objects.create(
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            phone=self.clean_phone(),
            email=self.cleaned_data['email'],
            password=make_password(self.cleaned_data['password']),
            role='master'
        )
        
        # Теперь создаём профиль мастера
        master = super().save(commit=False)
        master.user = user
        
        if commit:
            master.save()
        
        return master


class MasterEditForm(forms.ModelForm):
    """Форма редактирования профиля мастера"""
    # Поля пользователя
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        label='Имя'
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        label='Фамилия'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control'
        }),
        label='Email'
    )
    
    # Поля мастера
    specialization = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        label='Специализация'
    )
    experience = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        label='Стаж (лет)',
        min_value=0
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4
        }),
        label='Описание'
    )
    photo = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        label='Фотография',
        required=False
    )
    
    class Meta:
        model = Masters
        fields = ['specialization', 'experience', 'description', 'photo']
    
    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        if self.user_instance:
            self.fields['first_name'].initial = self.user_instance.first_name
            self.fields['last_name'].initial = self.user_instance.last_name
            self.fields['email'].initial = self.user_instance.email
    
    def save(self, commit=True):
        master = super().save(commit=False)
        
        # Обновляем данные пользователя
        if self.user_instance:
            self.user_instance.first_name = self.cleaned_data['first_name']
            self.user_instance.last_name = self.cleaned_data['last_name']
            self.user_instance.email = self.cleaned_data['email']
            if commit:
                self.user_instance.save()
        
        if commit:
            master.save()
        
        return master


# ==================== ФОРМЫ УСЛУГ ====================

class ServiceForm(forms.ModelForm):
    """Форма создания/редактирования услуги"""
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Стрижка мужская'
        }),
        label='Название услуги'
    )
    category = forms.ChoiceField(
        choices=Services.CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Категория'
    )
    duration = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '30'
        }),
        label='Длительность (минут)',
        min_value=5
    )
    price = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1500.00',
            'step': '0.01'
        }),
        label='Цена (₽)',
        min_value=0,
        decimal_places=2,
        max_digits=10
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Описание услуги...'
        }),
        label='Описание'
    )
    
    class Meta:
        model = Services
        fields = ['name', 'category', 'duration', 'price', 'description']


# ==================== ФОРМЫ ЗАПИСЕЙ ====================

class BookingForm(forms.Form):
    """Форма записи на услугу (для клиентов)"""
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
            is_time_available = not Appointments.objects.filter(
                master=master,
                date=date,
                time=time,
                status__in=['confirmed', 'pending']
            ).exists()
            
            if not is_time_available:
                raise forms.ValidationError("Выбранное время уже занято. Пожалуйста, выберите другое время.")
        
        return cleaned_data


class AppointmentEditForm(forms.ModelForm):
    """Форма редактирования записи (для администратора/мастера)"""
    status = forms.ChoiceField(
        choices=Appointments.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Статус'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        label='Примечания',
        required=False
    )
    
    class Meta:
        model = Appointments
        fields = ['status', 'notes']


# ==================== ФОРМЫ ФОТО ====================

class PhotoForm(forms.ModelForm):
    """Форма загрузки фотографий"""
    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название фото'
        }),
        label='Название'
    )
    image = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        label='Изображение'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Описание (необязательно)'
        }),
        label='Описание',
        required=False
    )
    
    class Meta:
        model = Photo
        fields = ['title', 'image', 'description']