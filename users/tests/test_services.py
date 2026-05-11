import pytest
from unittest.mock import Mock, patch
import statistics
from django.contrib.auth.models import User
from django.utils import timezone
from users.models import Client
from cleaning.models import Order
from users.services import (
    get_client_orders,
    get_client_statistics,
    get_client_datetime_info,
    get_external_apis_data
)

@pytest.fixture
def test_client():
    user = User.objects.create(username="test_client_user")
    return Client.objects.create(user=user, phone="+375 (29) 111-22-33", birth_date="1990-01-01")

@pytest.fixture
def mock_orders(test_client):
    o1 = Order.objects.create(client=test_client, address="123 Apple St", date_execution=timezone.now())
    o2 = Order.objects.create(client=test_client, address="456 Banana Ave", date_execution=timezone.now())
    o3 = Order.objects.create(client=test_client, address="789 Apple Blvd", date_execution=timezone.now())
    return [o1, o2, o3]

@pytest.mark.django_db
class TestUsersServices:

    def test_get_client_orders(self, test_client, mock_orders):
        orders = get_client_orders(test_client)
        assert orders.count() == 3

    def test_get_client_orders_search(self, test_client, mock_orders):
        orders = get_client_orders(test_client, search_query="Apple")
        assert orders.count() == 2

    def test_get_client_orders_sort(self, test_client, mock_orders):
        orders = get_client_orders(test_client, sort_by='address')
        assert orders.first().address == "123 Apple St"
        assert orders.last().address == "789 Apple Blvd"

    def test_get_client_statistics_normal(self):
        o1 = Mock(status='paid')
        o1.get_total_cost.return_value = 100.0
        o2 = Mock(status='paid')
        o2.get_total_cost.return_value = 100.0
        o3 = Mock(status='paid')
        o3.get_total_cost.return_value = 250.0
        o4 = Mock(status='new')

        stats = get_client_statistics([o1, o2, o3, o4])

        assert stats['total_spent'] == 450.0
        assert stats['mean_spent'] == 150.0
        assert stats['median_spent'] == 100.0
        assert stats['mode_spent'] == 100.0

    def test_get_client_statistics_empty(self):
        stats = get_client_statistics([])
        assert stats['total_spent'] == 0
        assert stats['mean_spent'] == 0
        assert stats['median_spent'] == 0
        assert stats['mode_spent'] == 0

    @patch('users.services.statistics.mode')
    def test_get_client_statistics_no_mode(self, mock_mode):
        mock_mode.side_effect = statistics.StatisticsError
        o1 = Mock(status='paid')
        o1.get_total_cost.return_value = 100.0
        o2 = Mock(status='paid')
        o2.get_total_cost.return_value = 200.0

        stats = get_client_statistics([o1, o2])
        assert stats['mode_spent'] == "N/A (No exact mode)"

    def test_get_client_datetime_info(self):
        user = User(username="time_user", date_joined=timezone.now())
        info = get_client_datetime_info(user)

        assert 'current_timezone' in info
        assert 'date_local' in info
        assert 'date_utc' in info
        assert 'joined_local' in info
        assert 'joined_utc' in info
        assert 'text_calendar' in info

    @patch('users.services.requests.get')
    def test_get_external_apis_data_success(self, mock_get):
        def side_effect(url, *args, **kwargs):
            resp = Mock()
            if 'open-meteo' in url:
                resp.json.return_value = {'current_weather': {'temperature': 20.5}}
            elif 'adviceslip' in url:
                resp.json.return_value = {'slip': {'advice': "Clean your room"}}
            return resp

        mock_get.side_effect = side_effect

        data = get_external_apis_data()

        assert data['weather'] == "20.5°C in Minsk"
        assert data['advice'] == "Clean your room"

    @patch('users.services.requests.get')
    def test_get_external_apis_data_failures(self, mock_get):
        mock_get.side_effect = Exception("API Down")

        data = get_external_apis_data()

        assert data['weather'] == "Weather data unavailable"
        assert data['advice'] == "Keep your home clean and your mind clear!"