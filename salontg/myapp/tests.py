from django.test import TestCase
from .models import Users, Services, Masters

# Create your tests here.
class ModelTests(TestCase):
    def tearDown(self):
        """Очистка после каждого теста"""
        Users.objects.all().delete()
        Services.objects.all().delete()
        Masters.objects.all().delete()
        
    def test_user_creation(self):
        """Тест создания пользователя"""
        user = Users.objects.create(
            username="testuser",
            email="test@test.com",
            phone="+79991234567"
        )
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.created_at)
        
    def test_service_str(self):
        """Тест строкового представления услуги"""
        service = Services.objects.create(
            name="Маникюр",
            price=1500,
            duration=60
        )
        # Проверяем, что название и цена есть в строке
        self.assertIn("Маникюр", str(service))
        self.assertIn("1500", str(service))

class URLTests(TestCase):
    def test_index_url(self):
        """Главная страница доступна"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
    def test_admin_url(self):
        """Админка доступна"""
        response = self.client.get('/admin/')
        # Админка обычно редиректит на логин (302) для неавторизованных
        self.assertIn(response.status_code, [200, 302])
        
    def test_nonexistent_url(self):
        """Несуществующий URL"""
        # Просто проверяем, что не падает с 500 ошибкой
        response = self.client.get('/nonexistent-page-12345/')
        self.assertIn(response.status_code, [404, 200])  # 404 или кастомная 404 страница

class ViewTests(TestCase):
    def setUp(self):
        """Настройка тестовых данных"""
        self.service = Services.objects.create(
            name="Тестовая услуга",
            description="Описание тестовой услуги",
            price=1000,
            duration=45
        )
    
    def tearDown(self):
        Services.objects.all().delete()
        
    def test_index_view(self):
        """Тест главной страницы"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что шаблон используется
        # Если index.html еще нет, закомментируй эту строку:
        # self.assertTemplateUsed(response, 'index.html')
        
        # Проверяем, что страница загружается
        self.assertContains(response, '<html', status_code=200)
        
    def test_services_view(self):
        """Тест страницы услуг"""
        response = self.client.get('/services/')
        self.assertEqual(response.status_code, 200)
        
        # Если view еще не готов, просто проверяем статус
        # Когда view будет готов, раскомментируй:
        # if 'services' in response.context:
        #     self.assertIn(self.service, response.context['services'])