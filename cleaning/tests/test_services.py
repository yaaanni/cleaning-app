import pytest
from unittest.mock import patch
from datetime import date
from django.utils import timezone
from django.contrib.auth.models import User
from users.models import Client
from cleaning.models import ServiceType, Service, Order, OrderItem
from cleaning.services import (
    get_weather_api,
    get_exchange_rate_api,
    get_sales_statistics,
    get_popular_profitable_services,
    get_matplotlib_chart
)


@pytest.fixture
def mock_db_data():
    user = User.objects.create(username="stat_user")
    client = Client.objects.create(
        user=user,
        phone="+375 (29) 000-00-00",
        birth_date=date(1985, 5, 15)
    )

    type_a = ServiceType.objects.create(name="Standard Cleaning")
    type_b = ServiceType.objects.create(name="Deep Cleaning")

    service_a = Service.objects.create(service_type=type_a, name="Room Cleaning", price=20.00)
    service_b = Service.objects.create(service_type=type_b, name="Oven Cleaning", price=50.00)

    order1 = Order.objects.create(client=client, address="Street 1", date_execution=timezone.now(),
                                  status=Order.Status.PAID)
    order2 = Order.objects.create(client=client, address="Street 2", date_execution=timezone.now(),
                                  status=Order.Status.PAID)
    order3 = Order.objects.create(client=client, address="Street 3", date_execution=timezone.now(),
                                  status=Order.Status.NEW)

    OrderItem.objects.create(order=order1, service=service_a, quantity=3)
    OrderItem.objects.create(order=order2, service=service_b, quantity=1)
    OrderItem.objects.create(order=order3, service=service_a, quantity=1)


@patch('cleaning.services.requests.get')
def test_get_weather_api_success(mock_get):
    mock_get.return_value.json.return_value = {'current_weather': {'temperature': 22.5}}
    mock_get.return_value.raise_for_status.return_value = None

    result = get_weather_api()
    assert result == 22.5
    mock_get.assert_called_once()


@patch('cleaning.services.requests.get')
def test_get_weather_api_exception(mock_get):
    mock_get.side_effect = Exception("Connection Timeout")

    result = get_weather_api()
    assert result is None


@patch('cleaning.services.requests.get')
def test_get_exchange_rate_api_success(mock_get):
    mock_get.return_value.json.return_value = {'rates': {'USD': 0.31}}
    mock_get.return_value.raise_for_status.return_value = None

    result = get_exchange_rate_api()
    assert result == 0.31
    mock_get.assert_called_once()


@patch('cleaning.services.requests.get')
def test_get_exchange_rate_api_exception(mock_get):
    mock_get.side_effect = Exception("API Unavailable")

    result = get_exchange_rate_api()
    assert result is None


@pytest.mark.django_db
def test_get_sales_statistics(mock_db_data):
    stats = get_sales_statistics()

    assert stats['total_sales'] == 110.00
    assert stats['mean_sales'] == 55.00
    assert stats['median_sales'] == 55.00
    assert isinstance(stats['mean_age'], (int, float))
    assert isinstance(stats['median_age'], (int, float))


@pytest.mark.django_db
def test_get_sales_statistics_empty():
    stats = get_sales_statistics()

    assert stats['total_sales'] == 0
    assert stats['mean_sales'] == 0
    assert stats['median_sales'] == 0


@pytest.mark.django_db
def test_get_popular_profitable_services(mock_db_data):
    popular, profitable, chart_data = get_popular_profitable_services()

    assert popular == "Standard Cleaning"
    assert profitable == "Standard Cleaning"
    assert "Standard Cleaning" in chart_data['labels']
    assert "Deep Cleaning" in chart_data['labels']
    assert len(chart_data['data']) == 2


@pytest.mark.django_db
def test_get_popular_profitable_services_empty():
    popular, profitable, chart_data = get_popular_profitable_services()

    assert popular is None
    assert profitable is None
    assert chart_data == []


@pytest.mark.django_db
def test_get_matplotlib_chart(mock_db_data):
    chart_uri = get_matplotlib_chart()

    assert chart_uri is not None
    assert isinstance(chart_uri, str)


@pytest.mark.django_db
def test_get_matplotlib_chart_empty():
    chart_uri = get_matplotlib_chart()

    assert chart_uri is None