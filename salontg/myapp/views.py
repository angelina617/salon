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
    # Получаем популярные услуги (можно добавить поле is_popular в модель)
    popular_services = Services.objects.all()[:4]  # Временно берем первые 4
    
    # Получаем мастеров для отображения на главной
    featured_masters = Masters.objects.all()[:4]  # Временно берем первых 4
    
    # Статистика (пример)
    stats = {
        'masters_count': Masters.objects.count(),
        'services_count': Services.objects.count(),
        'happy_clients': Users.objects.filter(role='client').count()  # Пример
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
    
    # Получаем все услуги
    services_list = Services.objects.all()
    
    # Применяем фильтры
    if category_filter:
        services_list = services_list.filter(category=category_filter)
    
    if search_query:
        services_list = services_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Пагинация
    paginator = Paginator(services_list, 9)  # 9 услуг на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем уникальные категории для фильтра
    categories = Services.objects.values_list('category', 'category').distinct()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': search_query,
    }
    
    return render(request, 'services.html', context)

def service_detail_page(request, service_id):
    service = get_object_or_404(Services, id=service_id)
    masters = Masters.objects.all()
    
    context = {
        'service': service,
        'masters': masters,
        'user': request.session.get('user')
    }
    
    return render(request, 'service_detail.html', context)

def masters_page(request):
    specialization_filter = request.GET.get('specialization', '')
    search_query = request.GET.get('search', '')
    
    # Получаем всех мастеров
    masters_list = Masters.objects.select_related('user').all()
    
    # Применяем фильтры
    if specialization_filter:
        masters_list = masters_list.filter(specialization__icontains=specialization_filter)
    
    if search_query:
        masters_list = masters_list.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Пагинация
    paginator = Paginator(masters_list, 12)  # 12 мастеров на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем уникальные специализации
    specializations = Masters.objects.values_list('specialization', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'specializations': specializations,
        'selected_specialization': specialization_filter,
        'search_query': search_query,
    }
    
    return render(request, 'masters.html', context)

# Детальная страница мастера
def master_detail_page(request, master_id):
    master = get_object_or_404(Masters, id=master_id)
    
    # Получаем услуги, которые предоставляет мастер
    services = Services.objects.all()[:5]
    
    upcoming_appointments = Appointments.objects.filter(
        master=master,
        date__gte=date.today(),
        status='confirmed'
    ).order_by('date', 'time')[:5]
    
    context = {
        'master': master,
        'services': services,
        'upcoming_appointments': upcoming_appointments,
        'user': request.session.get('user')
    }
    
    return render(request, 'master_detail.html', context)

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
        # Получаем данные из формы
        client_name = request.POST.get('client_name')
        client_phone = request.POST.get('client_phone')
        client_email = request.POST.get('client_email')
        service_id = request.POST.get('service')
        master_id = request.POST.get('master')
        appointment_date = request.POST.get('date')
        appointment_time = request.POST.get('time')
        notes = request.POST.get('notes', '')
        
        try:
            # Получаем объекты
            service = Services.objects.get(id=service_id)
            master = Masters.objects.get(id=master_id)
            
            # Проверяем доступность времени
            is_time_available = not Appointments.objects.filter(
                master=master,
                date=appointment_date,
                time=appointment_time,
                status__in=['confirmed', 'pending']
            ).exists()
            
            if not is_time_available:
                error = "Выбранное время уже занято. Пожалуйста, выберите другое время."
            else:
                # Создаем пользователя (или находим существующего)
                user, created = Users.objects.get_or_create(
                    phone=client_phone,
                    defaults={
                        'first_name': client_name.split()[0] if client_name else 'Клиент',
                        'last_name': ' '.join(client_name.split()[1:]) if client_name and len(client_name.split()) > 1 else '',
                        'email': client_email,
                        'password': 'default_password',  # В реальном проекте нужно генерировать
                        'role': 'client',
                    }
                )
                
                # Создаем запись
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
    
    # Получаем данные для формы
    services = Services.objects.all()
    masters = Masters.objects.all()
    
    # Если передан мастер или услуга в GET-параметрах
    selected_master_id = request.GET.get('master_id')
    selected_service_id = request.GET.get('service_id')
    
    selected_master = None
    selected_service = None
    
    if selected_master_id:
        try:
            selected_master = Masters.objects.get(id=selected_master_id)
        except Masters.DoesNotExist:
            pass
    
    if selected_service_id:
        try:
            selected_service = Services.objects.get(id=selected_service_id)
        except Services.DoesNotExist:
            pass
    
    # Получаем занятое время для календаря (если выбраны мастер и дата)
    busy_times = []
    master_id_for_calendar = request.GET.get('master_for_calendar')
    date_for_calendar = request.GET.get('date_for_calendar')
    
    if master_id_for_calendar and date_for_calendar:
        busy_times = Appointments.objects.filter(
            master_id=master_id_for_calendar,
            date=date_for_calendar,
            status__in=['confirmed', 'pending']
        ).values_list('time', flat=True)
    
    context = {
        'services': services,
        'masters': masters,
        'selected_master': selected_master,
        'selected_service': selected_service,
        'error': error,
        'success_message': success_message,
        'busy_times': busy_times,
        'today': date.today().isoformat(),
    }
    
    return render(request, 'booking.html', context)

# РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ

def register_page(request):
    """Страница регистрации с использованием формы"""
    if request.method == 'POST':
        # Создаем форму с данными из POST-запроса
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            # form.cleaned_data содержит валидированные данные
            # commit=False означает: создай объект, но не сохраняй в базу пока
            user = form.save(commit=False)
            
            # Хэшируем пароль (форма уже проверила, что пароли совпадают)
            user.password = make_password(form.cleaned_data['password'])
            user.role = 'client'
            user.save()  # Теперь сохраняем в базу
            
            # Автоматически авторизуем пользователя
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
        
        # Если форма невалидна, Django сохранит ошибки в form.errors
        # и мы вернем форму с ошибками пользователю
        # НЕТ НЕОБХОДИМОСТИ ВРУЧНУЮ ВЫВОДИТЬ СООБЩЕНИЯ - форма сама покажет ошибки в шаблоне
    
    else:  # GET запрос - показываем пустую форму
        form = RegisterForm()
    
    # Рендерим шаблон с формой
    return render(request, 'register.html', {'form': form})

def login_page(request):
    """Страница входа"""
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        
        if not phone or not password:
            messages.error(request, 'Введите телефон и пароль.')
            return render(request, 'login.html')
        
        try:
            # Ищем пользователя
            user = Users.objects.get(phone=phone)
            
            # Проверяем пароль
            if check_password(password, user.password):
                # Сохраняем пользователя в сессии
                request.session['user_id'] = user.id
                request.session['user'] = {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'email': user.email,
                    'role': user.role
                }
                
                messages.success(request, f'Добро пожаловать, {user.first_name}!')
                return redirect('index')
            else:
                messages.error(request, 'Неверный пароль.')
                
        except Users.DoesNotExist:
            messages.error(request, 'Пользователь с таким телефоном не найден.')
    
    return render(request, 'login.html')

def logout_page(request):
    """Выход из системы"""
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'user' in request.session:
        del request.session['user']
    
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('index')

# ЛИЧНЫЙ КАБИНЕТ

def profile_page(request):
    """Личный кабинет пользователя"""
    # Проверяем авторизацию
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Для доступа к личному кабинету необходимо авторизоваться.')
        return redirect('login')
    
    try:
        user = Users.objects.get(id=user_id)
        
        # Получаем все записи пользователя
        appointments = Appointments.objects.filter(client=user).order_by('-date', '-time')
        
        # Разделяем записи на будущие и прошедшие
        today = date.today()
        now = datetime.now().time()
        
        future_appointments = []
        past_appointments = []
        
        for appointment in appointments:
            if appointment.date > today or (appointment.date == today and appointment.time > now):
                future_appointments.append(appointment)
            else:
                past_appointments.append(appointment)
        
        context = {
            'user': request.session.get('user'),
            'future_appointments': future_appointments,
            'past_appointments': past_appointments,
        }
        
        return render(request, 'profile.html', context)
        
    except Users.DoesNotExist:
        # Если пользователь не найден, очищаем сессию
        if 'user_id' in request.session:
            del request.session['user_id']
        if 'user' in request.session:
            del request.session['user']
        
        messages.error(request, 'Пользователь не найден.')
        return redirect('login')

def cancel_appointment(request, appointment_id):
    """Отмена записи"""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Для отмены записи необходимо авторизоваться.')
        return redirect('login')
    
    try:
        appointment = Appointments.objects.get(id=appointment_id, client_id=user_id)
        
        # Можно отменять только будущие записи
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
        
        return redirect('profile')
        
    except Appointments.DoesNotExist:
        messages.error(request, 'Запись не найдена или у вас нет прав для ее отмены.')
        return redirect('profile')