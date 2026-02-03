from django.contrib import admin
from .models import Users, Services, Masters, Appointments

# Register your models here.
@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'email', 'role')
    list_filter = ('role',)
    search_fields = ('first_name', 'last_name', 'phone', 'email')

@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'duration', 'price')
    list_filter = ('category',)
    search_fields = ('name', 'description')

@admin.register(Masters)
class MastersAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'specialization', 'experience')
    search_fields = ('user__first_name', 'user__last_name', 'specialization')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Мастер'

@admin.register(Appointments)
class AppointmentsAdmin(admin.ModelAdmin):
    list_display = ('client', 'service', 'master', 'date', 'time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('client__first_name', 'client__last_name', 'master__user__first_name')