from django.shortcuts import render, redirect, get_object_or_404
from .models import Users, Services, Masters, Appointments
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import date, datetime
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .forms import RegisterForm, LoginForm, BookingForm

# Create your views here.
def index_page(request):
    popular_services = Services.objects.all()[:4]
    featured_masters = Masters.objects.all()[:4]
    
    stats = {
        'masters_count': Masters.objects.count(),
        'services_count': Services.objects.count(),
        'happy_clients': Users.objects.filter(role='client').count()
    }
    
    context = {
        'popular_services': popular_services,
        'featured_masters': featured_masters,
        'stats': stats,
    }
    
    return render(request, 'index.html', context)

def services_page(request):
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    # Получаем все услуги из базы данных
    services_list = Services.objects.all().order_by('id')
    
    # Фильтр по категории (это просто CharField с choices)
    if category_filter:
        services_list = services_list.filter(category=category_filter)
    
    # Поиск по названию и описанию
    if search_query:
        services_list = services_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Пагинация (9 услуг на страницу)
    paginator = Paginator(services_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем уникальные категории из базы данных
    categories = Services.objects.values_list('category', flat=True).distinct()
    
    # Преобразуем коды категорий в человекочитаемые названия
    category_display = dict(Services.CATEGORY_CHOICES)
    categories_display = [
        {'code': cat, 'name': category_display.get(cat, cat)}
        for cat in categories
    ]
    
    context = {
        'page_obj': page_obj,
        'categories': categories_display,
        'selected_category': category_filter,
        'search_query': search_query,
    }
    
    return render(request, 'services.html', context)

# УДАЛЕНО: service_detail_page (нет соответствующего шаблона в списке)
# Ссылки на детали услуги должны вести на services_page с фильтром или обрабатываться через JS

def masters_page(request):
    specialization_filter = request.GET.get('specialization', '')
    search_query = request.GET.get('search', '')
    
    masters_list = Masters.objects.select_related('user').all()
    
    if specialization_filter:
        masters_list = masters_list.filter(specialization__icontains=specialization_filter)
    
    if search_query:
        masters_list = masters_list.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(masters_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    specializations = Masters.objects.values_list('specialization', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'specializations': specializations,
        'selected_specialization': specialization_filter,
        'search_query': search_query,
    }
    
    return render(request, 'masters.html', context)

# УДАЛЕНО: master_detail_page (нет соответствующего шаблона в списке)
# Детали мастера должны отображаться через модальные окна на masters_page или services_page

def promotions_page(request):
    promotions = [
        {
            'title': 'Скидка 20% на первое посещение',
            'description': 'Для новых клиентов действует скидка 20% на любую услугу при первом посещении',
            'valid_until': '31.12.2024',
        },
        {
            'title': 'Комплекс услуг со скидкой 15%',
            'description': 'При заказе комплекса из 3 и более услуг действует скидка 15%',
            'valid_until': '30.11.2024',
        },
        {
            'title': 'Подарочный сертификат',
            'description': 'При покупке подарочного сертификата от 5000 рублей - дополнительная услуга в подарок',
            'valid_until': '01.01.2025',
        },
    ]
    
    context = {
        'promotions': promotions,
    }
    
    return render(request, 'promotions.html', context)

def booking_page(request):
    error = None
    success_message = None
    
    if request.method == 'POST':
        client_name = request.POST.get('client_name')
        client_phone = request.POST.get('client_phone')
        client_email = request.POST.get('client_email')
        service_id = request.POST.get('service')
        master_id = request.POST.get('master')
        appointment_date = request.POST.get('date')
        appointment_time = request.POST.get('time')
        notes = request.POST.get('notes', '')
        
        try:
            service = Services.objects.get(id=service_id)
            master = Masters.objects.get(id=master_id)
            
            is_time_available = not Appointments.objects.filter(
                master=master,
                date=appointment_date,
                time=appointment_time,
                status__in=['confirmed', 'pending']
            ).exists()
            
            if not is_time_available:
                error = "Выбранное время уже занято. Пожалуйста, выберите другое время."
            else:
                user, created = Users.objects.get_or_create(
                    phone=client_phone,
                    defaults={
                        'first_name': client_name.split()[0] if client_name else 'Клиент',
                        'last_name': ' '.join(client_name.split()[1:]) if client_name and len(client_name.split()) > 1 else '',
                        'email': client_email,
                        'password': make_password('default_temp_password'),
                        'role': 'client',
                    }
                )
                
                appointment = Appointments.objects.create(
                    client=user,
                    master=master,
                    service=service,
                    date=appointment_date,
                    time=appointment_time,
                    notes=notes,
                    status='pending'
                )
                
                success_message = f"Запись успешно создана! Номер записи: {appointment.id}. Мы свяжемся с вами для подтверждения."
                
        except Services.DoesNotExist:
            error = "Выбранная услуга не найдена."
        except Masters.DoesNotExist:
            error = "Выбранный мастер не найден."
        except Exception as e:
            error = f"Произошла ошибка: {str(e)}"
    
    services = Services.objects.all()
    masters = Masters.objects.all()
    
    selected_master_id = request.GET.get('master_id')
    selected_service_id = request.GET.get('service_id')
    
    selected_master = Masters.objects.filter(id=selected_master_id).first() if selected_master_id else None
    selected_service = Services.objects.filter(id=selected_service_id).first() if selected_service_id else None
    
    busy_times = []
    master_id_for_calendar = request.GET.get('master_for_calendar')
    date_for_calendar = request.GET.get('date_for_calendar')
    
    if master_id_for_calendar and date_for_calendar:
        busy_times = list(Appointments.objects.filter(
            master_id=master_id_for_calendar,
            date=date_for_calendar,
            status__in=['confirmed', 'pending']
        ).values_list('time', flat=True))
    
    # Передаем user в контекст для отображения в шапке (если авторизован)
    current_user = request.session.get('user')
    
    context = {
        'services': services,
        'masters': masters,
        'selected_master': selected_master,
        'selected_service': selected_service,
        'error': error,
        'success_message': success_message,
        'busy_times': busy_times,
        'today': date.today().isoformat(),
        'user': current_user,  # Для отображения статуса авторизации в шапке
    }
    
    return render(request, 'booking.html', context)

# РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ
# Шаблоны register.html и login.html должны существовать в проекте (не входят в основной список,
# но критичны для работы). Если их нет - создайте на базе base.html

def register_page(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.role = 'client'
            user.save()
            
            request.session['user_id'] = user.id
            request.session['user'] = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'email': user.email,
                'role': user.role
            }
            
            messages.success(request, f'Регистрация прошла успешно! Добро пожаловать, {user.first_name}!')
            return redirect('index')
        
        else:
            # ← Добавьте эту строку для отладки
            print("Form errors:", form.errors)


    else:
        form = RegisterForm()
    
    return render(request, 'register.html', {'form': form})

def login_page(request):
    form = LoginForm()

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        
        if not phone or not password:
            messages.error(request, 'Введите телефон и пароль.')
        else:
            try:
                user = Users.objects.get(phone=phone)
                if check_password(password, user.password):
                    request.session['user_id'] = user.id
                    request.session['user'] = {
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'phone': user.phone,
                        'email': user.email,
                        'role': user.role,
                        'username': user.phone
                    }
                    messages.success(request, f'Добро пожаловать, {user.first_name}!')
                    return redirect('index')
                else:
                    messages.error(request, 'Неверный пароль.')
            except Users.DoesNotExist:
                messages.error(request, 'Пользователь с таким телефоном не найден.')
    
    return render(request, 'login.html', {'form': form})

def logout_page(request):
    request.session.flush()
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('index')

# ЛИЧНЫЙ КАБИНЕТ (ИСПОЛЬЗУЕТ client.html ИЗ СПИСКА)
def profile_page(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Для доступа к личному кабинету необходимо авторизоваться.')
        return redirect('login')
    
    try:
        user = Users.objects.get(id=user_id)
        appointments = Appointments.objects.filter(client=user).order_by('-date', '-time')
        
        today = date.today()
        now = datetime.now().time()
        
        future_appointments = []
        past_appointments = []
        
        for appointment in appointments:
            if appointment.date > today or (appointment.date == today and appointment.time > now):
                future_appointments.append(appointment)
            else:
                past_appointments.append(appointment)
        
        # ВАЖНО: шаблон client.html ожидает переменные:
        # - user (данные пользователя из сессии)
        # - future_appointments / past_appointments
        # - возможно, другие переменные из контекста
        context = {
            'user': request.session.get('user'),
            'future_appointments': future_appointments,
            'past_appointments': past_appointments,
        }
        
        return render(request, 'client.html', context)  # ИЗМЕНЕНО: profile.html → client.html
        
    except Users.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Пользователь не найден.')
        return redirect('login')

def cancel_appointment(request, appointment_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Для отмены записи необходимо авторизоваться.')
        return redirect('login')
    
    try:
        appointment = Appointments.objects.get(id=appointment_id, client_id=user_id)
        
        today = date.today()
        now = datetime.now().time()
        
        if appointment.date < today or (appointment.date == today and appointment.time < now):
            messages.error(request, 'Нельзя отменить прошедшую запись.')
        elif appointment.status in ['cancelled', 'completed', 'no_show']:
            messages.error(request, 'Эта запись уже имеет финальный статус.')
        else:
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, 'Запись успешно отменена.')
        
        return redirect('client')  # Перенаправление на маршрут профиля
        
    except Appointments.DoesNotExist:
        messages.error(request, 'Запись не найдена или у вас нет прав для ее отмены.')
        return redirect('profile')

# ДОПОЛНИТЕЛЬНО: Представление для админ-панели (если потребуется)
def admin_panel(request):
    """Простая заглушка для админ-панели. Требует доработки и защиты!"""
    if not request.session.get('user'):
        messages.warning(request, 'Требуется авторизация.')
        return redirect('login')
    
    # Добавьте проверку роли администратора в продакшене!
    # if request.session['user'].get('role') != 'admin':
    #     messages.error(request, 'Доступ запрещен.')
    #     return redirect('index')
    
    # Здесь можно добавить логику загрузки данных для CRM
    context = {
        'user': request.session.get('user'),
        # Добавьте нужные данные для админки
    }
    return render(request, 'admin.html', context)

def master_dashboard(request):
    """Страница мастера - просмотр своих записей"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Для доступа к личному кабинету мастера необходимо авторизоваться.')
        return redirect('login')
    
    try:
        # Получаем пользователя
        user = Users.objects.get(id=user_id)
        
        # Проверяем, что пользователь - мастер
        if user.role != 'master':
            messages.error(request, 'У вас нет доступа к этой странице.')
            return redirect('index')
        
        # Получаем профиль мастера
        master_profile = Masters.objects.get(user=user)
        
        # Получаем все записи к этому мастеру
        appointments = Appointments.objects.filter(master=master_profile).select_related(
            'client', 'service'
        ).order_by('-date', '-time')
        
        today = date.today()
        now = datetime.now().time()
        
        # Разделяем на будущие и прошедшие записи
        future_appointments = []
        past_appointments = []
        
        for appointment in appointments:
            if appointment.date > today or (appointment.date == today and appointment.time > now):
                future_appointments.append(appointment)
            else:
                past_appointments.append(appointment)
        
        context = {
            'user': request.session.get('user'),
            'master': master_profile,
            'future_appointments': future_appointments,
            'past_appointments': past_appointments,
            'today': today,
        }
        
        return render(request, 'master_dashboard.html', context)
        
    except Users.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Пользователь не найден.')
        return redirect('login')
    except Masters.DoesNotExist:
        messages.error(request, 'Профиль мастера не найден.')
        return redirect('index')
    
def master_confirm_appointment(request, appointment_id):
    """Подтверждение записи мастером"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Необходимо авторизоваться.')
        return redirect('login')
    
    try:
        user = Users.objects.get(id=user_id)
        
        if user.role != 'master':
            messages.error(request, 'У вас нет прав для выполнения этого действия.')
            return redirect('index')
        
        master_profile = Masters.objects.get(user=user)
        
        appointment = Appointments.objects.get(id=appointment_id, master=master_profile)
        
        if appointment.status == 'cancelled':
            messages.error(request, 'Нельзя подтвердить отменённую запись.')
        elif appointment.status == 'completed':
            messages.error(request, 'Запись уже завершена.')
        else:
            appointment.status = 'confirmed'
            appointment.save()
            messages.success(request, 'Запись успешно подтверждена!')
        
        return redirect('master_dashboard')
        
    except (Users.DoesNotExist, Masters.DoesNotExist, Appointments.DoesNotExist):
        messages.error(request, 'Запись не найдена.')
        return redirect('master_dashboard')
    
def master_complete_appointment(request, appointment_id):
    """Завершение записи мастером"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Необходимо авторизоваться.')
        return redirect('login')
    
    try:
        user = Users.objects.get(id=user_id)
        
        if user.role != 'master':
            messages.error(request, 'У вас нет прав для выполнения этого действия.')
            return redirect('index')
        
        master_profile = Masters.objects.get(user=user)
        
        appointment = Appointments.objects.get(id=appointment_id, master=master_profile)
        
        if appointment.status == 'cancelled':
            messages.error(request, 'Нельзя завершить отменённую запись.')
        elif appointment.status == 'completed':
            messages.error(request, 'Запись уже завершена.')
        else:
            appointment.status = 'completed'
            appointment.save()
            messages.success(request, 'Запись успешно завершена!')
        
        return redirect('master_dashboard')
        
    except (Users.DoesNotExist, Masters.DoesNotExist, Appointments.DoesNotExist):
        messages.error(request, 'Запись не найдена.')
        return redirect('master_dashboard')