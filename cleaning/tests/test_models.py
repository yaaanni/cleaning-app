import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from users.models import Client
from content.models import PromoCode
from cleaning.models import ServiceType, Service, Order, OrderItem


@pytest.fixture
def test_client():
    user = User.objects.create(username="testclient")
    return Client.objects.create(
        user=user,
        phone="+375 (29) 111-22-33",
        birth_date="1990-01-01",
        client_type=Client.ClientType.INDIVIDUAL
    )


@pytest.fixture
def test_service_type():
    return ServiceType.objects.create(name="Deep Cleaning")


@pytest.fixture
def test_service(test_service_type):
    return Service.objects.create(
        service_type=test_service_type,
        name="Kitchen Cleaning",
        price=50.00
    )


@pytest.mark.django_db
class TestCleaningModels:

    def test_service_type_str(self, test_service_type):
        assert str(test_service_type) == "Deep Cleaning"

    def test_service_str(self, test_service):
        assert str(test_service) == "Kitchen Cleaning"

    def test_order_creation_and_str(self, test_client):
        order = Order.objects.create(
            client=test_client,
            address="123 Test St",
            date_execution=timezone.now() + timedelta(days=1)
        )
        assert str(order) == f"Order #{order.id}"
        assert order.status == Order.Status.NEW

    def test_order_item_price_freezing_and_str(self, test_client, test_service):
        order = Order.objects.create(
            client=test_client,
            address="123 Test St",
            date_execution=timezone.now() + timedelta(days=1)
        )
        item = OrderItem.objects.create(
            order=order,
            service=test_service,
            quantity=2
        )
        assert item.price == 50.00
        assert str(item) == f"2 x Kitchen Cleaning (Order #{order.id})"

    def test_order_item_get_cost(self, test_client, test_service):
        order = Order.objects.create(
            client=test_client,
            address="123 Test St",
            date_execution=timezone.now() + timedelta(days=1)
        )
        item = OrderItem.objects.create(
            order=order,
            service=test_service,
            quantity=3
        )
        assert item.get_cost() == 150.00

    def test_order_get_total_cost_no_promo(self, test_client, test_service):
        order = Order.objects.create(
            client=test_client,
            address="123 Test St",
            date_execution=timezone.now() + timedelta(days=1)
        )
        OrderItem.objects.create(order=order, service=test_service, quantity=2)
        OrderItem.objects.create(order=order, service=test_service, quantity=1)
        assert order.get_total_cost() == 150.00

    def test_order_get_total_cost_with_promo(self, test_client, test_service):
        promo = PromoCode.objects.create(code="DISCOUNT10", discount_percent=10)
        order = Order.objects.create(
            client=test_client,
            address="123 Test St",
            date_execution=timezone.now() + timedelta(days=1),
            promo_code=promo
        )
        OrderItem.objects.create(order=order, service=test_service, quantity=2)
        assert order.get_total_cost() == 90.00