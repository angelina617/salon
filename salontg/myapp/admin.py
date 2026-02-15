from django.contrib import admin
from .models import Users, Services, Masters, Appointments
from django.contrib.auth.hashers import make_password

# Register your models here.
@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'email', 'role')
    list_filter = ('role',)
    search_fields = ('first_name', 'last_name', 'phone', 'email')

    # Автоматически хешируем пароль при сохранении через админку
    def save_model(self, request, obj, form, change):
        # Если пароль был изменён (не начинается с хеша)
        if obj.password and not obj.password.startswith('pbkdf2_sha256$'):
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'duration', 'price')
    list_filter = ('category',)
    search_fields = ('name', 'description')

@admin.register(Masters)
class MastersAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'specialization', 'experience')
    search_fields = ('user__first_name', 'user__last_name', 'specialization')
    filter_horizontal = ['services']  # ← Удобный выбор услуг
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Мастер'

@admin.register(Appointments)
class AppointmentsAdmin(admin.ModelAdmin):
    list_display = ('client_info', 'service_info', 'master_info', 'date', 'time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('client__first_name', 'client__last_name', 'master__user__first_name')
    
    def client_info(self, obj):
        if obj.client:
            return f"{obj.client.first_name} {obj.client.last_name}"
        return "-"
    client_info.short_description = 'Клиент'
    
    def service_info(self, obj):
        return obj.service.name if obj.service else "-"
    service_info.short_description = 'Услуга'
    
    def master_info(self, obj):
        if obj.master and obj.master.user:
            return obj.master.user.first_name
        return "-"
    master_info.short_description = 'Мастер'