import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import PermissionDenied
from users.models import Client, Employee, Specialization
from cleaning.models import ServiceType, Service, Order, OrderItem
from users.views import (
    ContactsListView, RegisterView, ClientProfileView,
    EmployeeProfileView, SuperuserDashboardView
)

@pytest.fixture
def setup_users_data(db):
    client_u = User.objects.create_user(username="c_user", password="123")
    client_p = Client.objects.create(user=client_u, phone="111", birth_date="1990-01-01")

    emp_u = User.objects.create_user(username="e_user", password="123")
    emp_p = Employee.objects.create(user=emp_u, phone="222", email="e@e.com", birth_date="1980-01-01")

    norm_u = User.objects.create_user(username="n_user", password="123")
    admin_u = User.objects.create_superuser(username="admin", password="123")

    st = ServiceType.objects.create(name="Cleaning")
    s = Service.objects.create(service_type=st, name="Room", price=50)

    order = Order.objects.create(
        client=client_p,
        employee=emp_p,
        address="Minsk",
        date_execution=timezone.now() + timedelta(days=2),
        status=Order.Status.PAID
    )
    OrderItem.objects.create(order=order, service=s, quantity=2)

    return {
        'c_user': client_u,
        'c_profile': client_p,
        'e_user': emp_u,
        'e_profile': emp_p,
        'n_user': norm_u,
        'admin': admin_u,
        'order': order,
        'service': s
    }

@pytest.mark.django_db
class TestUserViews:

    def test_contacts_list_view(self, rf, setup_users_data):
        request = rf.get('/contacts/')
        view = ContactsListView.as_view()
        response = view(request)
        assert response.status_code == 200
        assert 'employees' in response.context_data

    def test_register_view(self, rf):
        request = rf.get('/register/')
        view = RegisterView.as_view()
        response = view(request)
        assert response.status_code == 200

    @patch('users.views.get_external_apis_data')
    @patch('users.views.get_client_datetime_info')
    @patch('users.views.get_client_statistics')
    @patch('users.views.get_client_orders')
    def test_client_profile_view_is_client(self, mock_orders, mock_stats, mock_dt, mock_apis, rf, setup_users_data):
        mock_orders.return_value = []
        mock_stats.return_value = {'total_spent': 100}
        mock_dt.return_value = {'date_local': 'today'}
        mock_apis.return_value = {'weather': '20C'}

        request = rf.get('/profile/?search=test&sort=date')
        request.user = setup_users_data['c_user']
        view = ClientProfileView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.context_data['is_client'] is True
        assert response.context_data['search_query'] == 'test'
        assert response.context_data['total_spent'] == 100
        assert response.context_data['weather'] == '20C'

    def test_client_profile_view_not_client(self, rf, setup_users_data):
        request = rf.get('/profile/')
        request.user = setup_users_data['n_user']
        view = ClientProfileView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.context_data['is_client'] is False

    def test_employee_profile_view_is_employee(self, rf, setup_users_data):
        request = rf.get('/emp-profile/')
        request.user = setup_users_data['e_user']
        view = EmployeeProfileView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.context_data['is_employee'] is True
        assert response.context_data['total_sales'] == 100
        assert response.context_data['completed_orders'] == 1
        assert response.context_data['total_orders'] == 1
        assert setup_users_data['c_profile'] in response.context_data['clients']

    def test_employee_profile_view_not_employee(self, rf, setup_users_data):
        request = rf.get('/emp-profile/')
        request.user = setup_users_data['n_user']
        view = EmployeeProfileView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.context_data['is_employee'] is False

    def test_superuser_dashboard_not_su(self, rf, setup_users_data):
        request = rf.get('/dashboard/')
        request.user = setup_users_data['n_user']
        view = SuperuserDashboardView.as_view()
        with pytest.raises(PermissionDenied):
            view(request)

    def test_superuser_dashboard_is_su(self, rf, setup_users_data):
        request = rf.get('/dashboard/')
        request.user = setup_users_data['admin']
        view = SuperuserDashboardView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert 'services' in response.context_data
        assert 'planned_orders' in response.context_data
        assert 'all_clients' in response.context_data
        assert 'all_employees' in response.context_data

    def test_superuser_dashboard_client_report(self, rf, setup_users_data):
        c_id = setup_users_data['c_profile'].id
        request = rf.get(f'/dashboard/?client_id={c_id}&start_date=2000-01-01&end_date=2030-01-01')
        request.user = setup_users_data['admin']
        view = SuperuserDashboardView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.context_data['report_client'] == setup_users_data['c_profile']
        assert response.context_data['report_client_cost'] == 100

    def test_superuser_dashboard_employee_report(self, rf, setup_users_data):
        e_id = setup_users_data['e_profile'].id
        request = rf.get(f'/dashboard/?employee_id={e_id}')
        request.user = setup_users_data['admin']
        view = SuperuserDashboardView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.context_data['report_employee'] == setup_users_data['e_profile']
        assert setup_users_data['c_profile'] in response.context_data['report_employee_clients']