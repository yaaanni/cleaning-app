import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from users.models import Client
from content.models import Vacancy
from cleaning.views import HomeDashboardView, VacancyListView


@pytest.fixture
def view_test_data():
    user1 = User.objects.create(username="user1", last_name="Anderson")
    user2 = User.objects.create(username="user2", last_name="Zimmerman")

    Client.objects.create(user=user1, phone="+375 (29) 111-11-11", birth_date="1990-01-01")
    Client.objects.create(user=user2, phone="+375 (29) 222-22-22", birth_date="1995-05-05")

    Vacancy.objects.create(title="Cleaner", description="Cleaning jobs", is_active=True)
    Vacancy.objects.create(title="Manager", description="Office jobs", is_active=False)


@pytest.mark.django_db
@patch('cleaning.views.get_matplotlib_chart')
@patch('cleaning.views.get_popular_profitable_services')
@patch('cleaning.views.get_sales_statistics')
@patch('cleaning.views.get_exchange_rate_api')
@patch('cleaning.views.get_weather_api')
def test_home_dashboard_view(mock_weather, mock_exchange, mock_stats, mock_pop, mock_chart, rf, view_test_data):
    mock_weather.return_value = 22.5
    mock_exchange.return_value = 3.15
    mock_stats.return_value = {'total_sales': 1000}
    mock_pop.return_value = ('Standard', 'Deep', {'labels': [], 'data': []})
    mock_chart.return_value = 'base64_encoded_string'

    request = rf.get('/?search=Ander&sort=-user__last_name')
    view = HomeDashboardView.as_view()
    response = view(request)

    assert response.status_code == 200

    context = response.context_data

    assert context['search_query'] == 'Ander'
    assert len(context['clients']) == 1
    assert context['clients'][0].user.last_name == 'Anderson'

    assert context['weather'] == 22.5
    assert context['exchange_rate'] == 3.15
    assert context['stats']['total_sales'] == 1000
    assert context['most_popular'] == 'Standard'
    assert context['most_profitable'] == 'Deep'
    assert context['matplotlib_chart'] == 'base64_encoded_string'

    assert 'current_timezone' in context
    assert 'date_local' in context
    assert 'date_utc' in context
    assert 'text_calendar' in context


@pytest.mark.django_db
def test_vacancy_list_view(rf, view_test_data):
    request = rf.get('/vacancies/')
    view = VacancyListView.as_view()
    response = view(request)

    assert response.status_code == 200

    context = response.context_data

    assert 'vacancies' in context
    assert len(context['vacancies']) == 1
    assert context['vacancies'][0].title == "Cleaner"
    assert context['vacancies'][0].is_active is True