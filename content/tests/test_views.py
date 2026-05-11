import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import User
from content.models import News, CompanyInfo, CompanyHistory, FAQ, Review, Vacancy, PromoCode
from cleaning.models import ServiceType, Service, Order, OrderItem
from users.models import Employee, Client, Specialization


@pytest.fixture
def setup_content_data(db):
    news = News.objects.create(title="News 1", short_content="Short", full_content="Full", image="test.jpg")
    company = CompanyInfo.objects.create(name="CleanCo", description="Desc", requisites="Req")
    history = CompanyHistory.objects.create(year=2020, description="Started")
    faq = FAQ.objects.create(question="Q?", answer="A!")
    vacancy = Vacancy.objects.create(title="Cleaner", description="Work", is_active=True)
    return {
        'news': news,
        'company': company,
        'history': history,
        'faq': faq,
        'vacancy': vacancy
    }


@pytest.fixture
def client_user(db):
    user = User.objects.create_user(username="client_user", password="password123")
    client_profile = Client.objects.create(
        user=user,
        phone="+375 (29) 111-22-33",
        birth_date="1990-01-01"
    )
    return user


@pytest.fixture
def employee_user(db):
    user = User.objects.create_user(username="staff_user", password="password123")
    emp = Employee.objects.create(
        user=user,
        phone="+375 (29) 444-55-66",
        email="staff@test.com",
        birth_date="1985-01-01",
        work_description="Expert"
    )
    return emp


@pytest.mark.django_db
class TestContentViews:

    def test_public_home_view(self, client, setup_content_data):
        url = reverse('content:public_home')
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['latest_news'] == setup_content_data['news']

    def test_about_company_view(self, client, setup_content_data):
        url = reverse('content:about_company')
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['company'] == setup_content_data['company']
        assert setup_content_data['history'] in response.context['history']

    def test_news_list_view(self, client, setup_content_data):
        url = reverse('content:news_list')
        response = client.get(url)
        assert response.status_code == 200
        assert setup_content_data['news'] in response.context['news_list']

    def test_news_detail_view(self, client, setup_content_data):
        url = reverse('content:news_detail', kwargs={'pk': setup_content_data['news'].pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['article'] == setup_content_data['news']

    def test_faq_list_view(self, client, setup_content_data):
        url = reverse('content:faq_list')
        response = client.get(url)
        assert response.status_code == 200
        assert setup_content_data['faq'] in response.context['faqs']

    def test_vacancy_list_view(self, client, setup_content_data):
        url = reverse('content:vacancy_list')
        response = client.get(url)
        assert response.status_code == 200
        assert setup_content_data['vacancy'] in response.context['vacancies']

    def test_review_post_as_client(self, client, client_user):
        client.login(username="client_user", password="password123")
        url = reverse('content:review_list')
        response = client.post(url, {'rating': 5, 'text': 'Excellent service!'})
        assert response.status_code == 302
        assert Review.objects.filter(text='Excellent service!').exists()

    def test_catalog_price_filtering(self, client):
        st = ServiceType.objects.create(name="Cleaning")
        Service.objects.create(service_type=st, name="Cheap", price=10)
        Service.objects.create(service_type=st, name="Expensive", price=100)

        url = reverse('content:catalog')
        response = client.get(url, {'min_price': '50', 'max_price': '150'})

        assert response.status_code == 200
        categories = response.context['categories']
        services = categories[0].services.all()
        assert len(services) == 1
        assert services[0].name == "Expensive"


@pytest.mark.django_db
class TestCartAndOrderProcess:

    def test_add_to_cart_authenticated(self, client, client_user):
        client.login(username="client_user", password="password123")
        st = ServiceType.objects.create(name="Type")
        service = Service.objects.create(service_type=st, name="Service", price=50)

        url = reverse('content:add_to_cart')
        response = client.post(url, {'service_id': service.id})

        assert response.status_code == 302
        assert client.session['cart'][str(service.id)] == 1

    def test_remove_from_cart(self, client, client_user):
        client.login(username="client_user", password="password123")
        session = client.session
        session['cart'] = {'1': 2}
        session.save()

        url = reverse('content:remove_from_cart')
        response = client.post(url, {'service_id': '1'})

        assert response.status_code == 302
        assert '1' not in client.session['cart']

    def test_order_checkout_full_cycle(self, client, client_user, employee_user):
        client.login(username="client_user", password="password123")

        st = ServiceType.objects.create(name="Windows")
        service = Service.objects.create(service_type=st, name="Window Cleaning", price=80)

        spec = Specialization.objects.create(name="WindowSpec")
        spec.service_types.add(st)
        employee_user.specializations.add(spec)

        session = client.session
        session['cart'] = {str(service.id): 1}
        session.save()

        url = reverse('content:cart')
        payload = {
            'address': 'Minsk, Main Str 1',
            'date_execution': '2026-05-20 12:00',
            'action': 'pay_later'
        }

        response = client.post(url, payload)

        assert response.status_code == 302
        assert Order.objects.filter(address='Minsk, Main Str 1').exists()
        order = Order.objects.get(address='Minsk, Main Str 1')
        assert order.employee == employee_user
        assert order.items.count() == 1
        assert 'cart' in client.session and client.session['cart'] == {}