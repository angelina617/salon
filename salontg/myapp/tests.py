from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, datetime
from django.contrib.auth.hashers import make_password, check_password
from .models import Users, Services, Masters, Appointments
from .forms import RegisterForm, LoginForm

class TestSalonViews(TestCase):
    def setUp(self):
        # Создаем тестовые данные
        self.client_user = Users.objects.create(
            first_name="Иван",
            last_name="Иванов",
            phone="12345678901",
            email="ivan@example.com",
            password=make_password("password123"),
            role="client"
        )
        
        self.master_user = Users.objects.create(
            first_name="Анна",
            last_name="Петрова",
            phone="12345678902",
            email="anna@example.com",
            password=make_password("password123"),
            role="master"
        )
        
        self.admin_user = Users.objects.create(
            first_name="Админ",
            last_name="Админов",
            phone="12345678903",
            email="admin@example.com",
            password=make_password("password123"),
            role="admin"
        )
        
        self.service = Services.objects.create(
            name="Классический маникюр",
            category="manicure",
            duration=60,
            price=1500.00,
            description="Профессиональный маникюр с покрытием"
        )
        
        self.master = Masters.objects.create(
            user=self.master_user,
            specialization="Маникюр",
            experience=5,
            description="Опытный мастер с 5-летним стажем"
        )
        
        # Создаем тестовую запись
        self.appointment = Appointments.objects.create(
            client=self.client_user,
            master=self.master,
            service=self.service,
            date=date.today(),
            time=time(10, 0),
            status="pending",
            notes="Без лака на ногтях"
        )
        
        # Создаем будущую запись для профиля
        self.future_appointment = Appointments.objects.create(
            client=self.client_user,
            master=self.master,
            service=self.service,
            date=date.today() + timezone.timedelta(days=1),
            time=time(11, 0),
            status="pending"
        )
        
        # Создаем прошедшую запись
        self.past_appointment = Appointments.objects.create(
            client=self.client_user,
            master=self.master,
            service=self.service,
            date=date.today() - timezone.timedelta(days=1),
            time=time(9, 0),
            status="confirmed"
        )
        
        # Инициализируем клиент
        self.client = Client()
        
        # Данные для тестирования форм
        self.valid_registration_data = {
            'first_name': 'Тест',
            'last_name': 'Тестов',
            'phone': '9998887766',
            'email': 'test@example.com',
            'password': 'password123',
            'password2': 'password123'
        }
        
        self.valid_login_data = {
            'phone': '9998887766',
            'password': 'password123'
        }

    # Тесты для моделей
    def test_users_str(self):
        self.assertEqual(str(self.client_user), "Иван Иванов (Клиент)")
        self.assertEqual(str(self.master_user), "Анна Петрова (Мастер)")
        self.assertEqual(str(self.admin_user), "Админ Админов (Администратор)")

    def test_services_str(self):
        self.assertEqual(str(self.service), "Классический маникюр")

    def test_masters_str(self):
        self.assertEqual(str(self.master), "Анна Петрова")

    def test_appointments_str(self):
        expected_str = f"{self.client_user} - {self.service} ({self.appointment.date} {self.appointment.time})"
        self.assertEqual(str(self.appointment), expected_str)

    # Тесты URL-маршрутов
    def test_index_page(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertIn('popular_services', response.context)
        self.assertIn('featured_masters', response.context)
        self.assertIn('stats', response.context)

    def test_services_page(self):
        response = self.client.get(reverse('services'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'services.html')
        self.assertIn('page_obj', response.context)
        self.assertIn('categories', response.context)

    def test_masters_page(self):
        response = self.client.get(reverse('masters'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'masters.html')
        self.assertIn('page_obj', response.context)
        self.assertIn('specializations', response.context)

    def test_promotions_page(self):
        response = self.client.get(reverse('promotions'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'promotions.html')
        self.assertIn('promotions', response.context)

    def test_booking_page_get(self):
        response = self.client.get(reverse('booking'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking.html')
        self.assertIn('services', response.context)
        self.assertIn('masters', response.context)
        self.assertIn('today', response.context)

    def test_register_page_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIsInstance(response.context['form'], RegisterForm)

    def test_login_page_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertIsInstance(response.context['form'], LoginForm)

    def test_client_profile_page(self):
        # Авторизуемся через сессию (кастомная аутентификация)
        session = self.client.session
        session['user_id'] = self.client_user.id
        session['user'] = {
            'id': self.client_user.id,
            'first_name': self.client_user.first_name,
            'last_name': self.client_user.last_name,
            'phone': self.client_user.phone,
            'email': self.client_user.email,
            'role': self.client_user.role,
            'username': self.client_user.phone
        }
        session.save()
        
        response = self.client.get(reverse('client'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'client.html')
        self.assertIn('future_appointments', response.context)
        self.assertIn('past_appointments', response.context)
        self.assertEqual(len(response.context['future_appointments']), 2)
        self.assertEqual(len(response.context['past_appointments']), 1)

    # Тесты представлений
    def test_registration(self):
        # Проверяем валидную регистрацию
        response = self.client.post(reverse('register'), self.valid_registration_data)
        self.assertRedirects(response, reverse('login'))
        
        # Проверяем, что пользователь создан
        self.assertEqual(Users.objects.count(), 4)  # 3 тестовых + 1 новый
        
        # Проверяем, что пользователь авторизован
        self.assertIn('user_id', self.client.session)
        
        # Проверяем невалидную регистрацию (пароли не совпадают)
        invalid_data = self.valid_registration_data.copy()
        invalid_data['password2'] = 'wrong_password'
        response = self.client.post(reverse('register'), invalid_data)
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        # Создаем пользователя для тестирования логина
        test_user = Users.objects.create(
            first_name="Тест",
            last_name="Тестов",
            phone="9998887766",
            email="test@example.com",
            password=make_password("password123"),
            role="client"
        )
        
        # Проверяем валидный логин
        response = self.client.post(reverse('login'), self.valid_login_data)
        self.assertRedirects(response, reverse('index'))
        
        # Проверяем, что пользователь авторизован
        self.assertIn('user_id', self.client.session)
        self.assertEqual(self.client.session['user']['first_name'], 'Тест')
        
        # Выходим из системы
        self.client.get(reverse('logout'))
        
        # Проверяем невалидный логин (неверный пароль)
        response = self.client.post(reverse('login'), {
            'phone': '9998887766',
            'password': 'wrong_password'
        })
        self.assertEqual(response.status_code, 200)

    def test_booking(self):
        # Авторизуемся через сессию
        session = self.client.session
        session['user_id'] = self.client_user.id
        session['user'] = {
            'id': self.client_user.id,
            'first_name': self.client_user.first_name,
            'last_name': self.client_user.last_name,
            'phone': self.client_user.phone,
            'email': self.client_user.email,
            'role': self.client_user.role
        }
        session.save()
        
        # Тестирование создания записи
        booking_data = {
            'client_name': 'Иван Иванов',
            'client_phone': self.client_user.phone,
            'client_email': self.client_user.email,
            'service': self.service.id,
            'master': self.master.id,
            'date': (date.today() + timezone.timedelta(days=2)).isoformat(),
            'time': '14:00',
            'notes': 'Тестовая запись'
        }
        
        response = self.client.post(reverse('booking'), booking_data)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что запись создана
        self.assertEqual(Appointments.objects.count(), 4)  # 3 тестовые + 1 новая
        
        # Проверяем, что время занято
        booking_data['time'] = '10:00'  # То же время, что и у существующей записи
        response = self.client.post(reverse('booking'), booking_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)

    def test_cancel_appointment(self):
        # Авторизуемся через сессию
        session = self.client.session
        session['user_id'] = self.client_user.id
        session['user'] = {
            'id': self.client_user.id,
            'first_name': self.client_user.first_name,
            'last_name': self.client_user.last_name,
            'phone': self.client_user.phone,
            'email': self.client_user.email,
            'role': self.client_user.role,
            'username': self.client_user.phone
        }
        session.save()
        
        # Проверяем успешную отмену
        response = self.client.get(reverse('cancel_appointment', args=[self.future_appointment.id]))
        self.assertRedirects(response, reverse('client'))
        
        # Обновляем запись из базы
        self.future_appointment.refresh_from_db()
        self.assertEqual(self.future_appointment.status, 'cancelled')
        
        # Создаем новую будущую запись для теста
        new_future_appointment = Appointments.objects.create(
            client=self.client_user,
            master=self.master,
            service=self.service,
            date=date.today() + timezone.timedelta(days=2),
            time=time(12, 0),
            status="pending"
        )
        
        # Проверяем отмену прошедшей записи
        response = self.client.get(reverse('cancel_appointment', args=[self.past_appointment.id]))
        self.assertRedirects(response, reverse('client'))
        
        # Обновляем запись из базы
        self.past_appointment.refresh_from_db()
        self.assertEqual(self.past_appointment.status, 'confirmed')  # Не должна измениться
        
        # Проверяем отмену записи с финальным статусом
        new_future_appointment.status = 'completed'
        new_future_appointment.save()
        response = self.client.get(reverse('cancel_appointment', args=[new_future_appointment.id]))
        self.assertRedirects(response, reverse('client'))
        
        # Обновляем запись из базы
        new_future_appointment.refresh_from_db()
        self.assertEqual(new_future_appointment.status, 'completed')  # Не должна измениться

    # Тесты для пагинации и фильтрации
    def test_services_pagination(self):
        # Создаем больше услуг для тестирования пагинации
        for i in range(10):
            Services.objects.create(
                name=f"Услуга {i}",
                category="manicure",
                duration=30,
                price=500.00,
                description=f"Описание {i}"
            )
        
        response = self.client.get(reverse('services') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 2)  # 9 на первой странице, 6 на второй

    def test_services_filtering(self):
        # Проверяем фильтрацию по категории
        response = self.client.get(reverse('services') + '?category=manicure')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 1)  # Только одна услуга в категории

        # Проверяем поиск
        response = self.client.get(reverse('services') + '?search=Классический')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 1)

    # Тесты админки
def test_users_admin(self):
    # Создаем администратора
    admin = Users.objects.create(
        first_name="Админ",
        last_name="Тест",
        phone="99999999999",
        email="admin@test.com",
        password=make_password("adminpass"),
        role="admin"
    )
    
    # Логинимся в админку
    self.client.force_login(admin)
    
    # Проверяем доступ к списку пользователей
    response = self.client.get('/admin/myapp/users/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Иван Иванов")

def test_services_admin(self):
    admin = Users.objects.create(
        first_name="Админ",
        last_name="Тест",
        phone="99999999998",
        email="admin2@test.com",
        password=make_password("adminpass"),
        role="admin"
    )
    
    self.client.force_login(admin)
    
    response = self.client.get('/admin/myapp/services/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Классический маникюр")

def test_masters_admin(self):
    admin = Users.objects.create(
        first_name="Админ",
        last_name="Тест",
        phone="99999999997",
        email="admin3@test.com",
        password=make_password("adminpass"),
        role="admin"
    )
    
    self.client.force_login(admin)
    
    response = self.client.get('/admin/myapp/masters/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Анна Петрова")

def test_appointments_admin(self):
    admin = Users.objects.create(
        first_name="Админ",
        last_name="Тест",
        phone="99999999996",
        email="admin4@test.com",
        password=make_password("adminpass"),
        role="admin"
    )
    
    self.client.force_login(admin)
    
    response = self.client.get('/admin/myapp/appointments/')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Иван Иванов")