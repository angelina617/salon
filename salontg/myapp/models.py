from django.db import models

# Create your models here.
class Users(models.Model):
    ROLE_CHOICES = [
        ('client', 'Клиент'),
        ('master', 'Мастер'),
        ('admin', 'Администратор'),
    ]

    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    phone = models.CharField(max_length=15, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    password = models.CharField(max_length=150, verbose_name='Пароль')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='Роль')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

class Services(models.Model):
    CATEGORY_CHOICES = [
        ('coloring','Окрашивание'),
        ('manicure', 'Маникюр'),
        ('massage', 'Массаж'),
        ('cosmetology', 'Косметология'),
    ]
    name = models.CharField(max_length=50, verbose_name='Название услуги')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name='Категория')
    duration = models.IntegerField(verbose_name='Длительность (мин)')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.name

class Masters(models.Model):
    class Meta:
        app_label = 'myapp'
    
    user = models.ForeignKey(Users, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='master_profile')
    specialization = models.CharField(max_length=50 , verbose_name='Специализация')
    services = models.ManyToManyField(Services, verbose_name='Услуги', related_name='masters')
    experience = models.IntegerField(verbose_name='Стаж')
    description = models.TextField(verbose_name='О мастере')
    photo = models.ImageField(
        verbose_name='Фотография мастера',
        upload_to='images/',  # папка для сохранения фотографий
        null=True,  # разрешаем NULL значения
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Appointments(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждение'),
        ('confirmed', 'Подтверждено'),
        ('complated', 'Завершена'),
        ('cancelled', 'Отменена'),
        ('no_show', 'Не пришёл'),
    ]

    user = models.ForeignKey(Users, on_delete=models.CASCADE, verbose_name='Клиент', related_name='appointments')
    master = models.ForeignKey(Masters, on_delete=models.CASCADE, verbose_name='Мастер', related_name='appointments')  
    service = models.ForeignKey(Services, on_delete=models.CASCADE, verbose_name='Услуга', related_name='appointments')    
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    notes = models.TextField(verbose_name='Примечания', blank=True)

    def __str__(self):
        return f"{self.user} - {self.service} ({self.date} {self.time})"

class Photo(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='photos/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title