import logging
from django.views.generic import ListView, CreateView, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from cleaning.models import Service
from django.utils import timezone
from .models import Employee, Client
from cleaning.models import Order
from .forms import ClientRegistrationForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .services import (
    get_client_orders,
    get_client_statistics,
    get_client_datetime_info,
    get_external_apis_data
)

logger = logging.getLogger(__name__)


class ContactsListView(ListView):
    model = Employee
    template_name = 'users/contacts.html'
    context_object_name = 'employees'

    def get_queryset(self):
        logger.info("Contacts list page accessed")
        return Employee.objects.select_related('user').prefetch_related('specializations').all()


class RegisterView(CreateView):
    form_class = ClientRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('content:public_home')

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(f"New client registered: {self.object.username}")
        return response


class ClientProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        logger.info(f"Client profile accessed by user: {self.request.user.username}")
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if hasattr(user, 'client_profile'):
            context['is_client'] = True
            client = user.client_profile
            context['profile'] = client

            search_query = self.request.GET.get('search', '')
            sort_by = self.request.GET.get('sort', '-date_created')

            logger.info(f"Client order filtering - Search: '{search_query}', Sort: {sort_by}")

            orders = get_client_orders(client, search_query, sort_by)
            context['orders'] = orders
            context['search_query'] = search_query

            stats = get_client_statistics(orders)
            context.update(stats)

            dt_info = get_client_datetime_info(user)
            context.update(dt_info)

            api_info = get_external_apis_data()
            context.update(api_info)
        else:
            logger.warning(f"User {user.username} tried to access client profile but has no profile object")
            context['is_client'] = False

        return context


class EmployeeProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/employee_profile.html'

    def get_context_data(self, **kwargs):
        logger.info(f"Employee profile accessed by user: {self.request.user.username}")
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if hasattr(user, 'employee_profile'):
            context['is_employee'] = True
            employee = user.employee_profile
            context['profile'] = employee

            orders = Order.objects.filter(employee=employee).order_by('-date_created')
            context['orders'] = orders

            paid_orders = [o for o in orders if o.status == 'paid']
            total_sales = sum(o.get_total_cost() for o in paid_orders)

            context['total_sales'] = total_sales
            context['completed_orders'] = len(paid_orders)
            context['total_orders'] = orders.count()

            logger.info(
                f"Employee {user.username} statistics - Total orders: {context['total_orders']}, Completed: {context['completed_orders']}")

            clients = Client.objects.filter(orders__employee=employee).distinct()
            context['clients'] = clients
        else:
            logger.warning(f"User {user.username} tried to access employee dashboard without employee profile")
            context['is_employee'] = False

        return context


class SuperuserDashboardView(UserPassesTestMixin, TemplateView):
    template_name = 'users/superuser_dashboard.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        logger.info(f"Superuser dashboard accessed by: {self.request.user.username}")
        context = super().get_context_data(**kwargs)

        context['planned_orders'] = Order.objects.filter(
            date_execution__gte=timezone.now(),
            status__in=[Order.Status.NEW, Order.Status.PAID]
        ).select_related('client__user').order_by('client', 'date_execution')

        context['all_clients'] = Client.objects.all()
        context['all_employees'] = Employee.objects.all()

        client_id = self.request.GET.get('client_id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if client_id and start_date and end_date:
            logger.info(f"Generating revenue report for Client ID: {client_id} from {start_date} to {end_date}")
            client_orders = Order.objects.filter(
                client_id=client_id,
                date_execution__gte=start_date,
                date_execution__lte=end_date
            ).exclude(status=Order.Status.CANCELLED)

            total_cost = sum(order.get_total_cost() for order in client_orders)
            context['report_client_cost'] = total_cost
            context['report_client'] = Client.objects.filter(id=client_id).first()
            context['report_start'] = start_date
            context['report_end'] = end_date

        employee_id = self.request.GET.get('employee_id')
        if employee_id:
            logger.info(f"Generating client list for Employee ID: {employee_id}")
            employee_clients = Client.objects.filter(
                orders__employee_id=employee_id
            ).distinct()
            context['report_employee_clients'] = employee_clients
            context['report_employee'] = Employee.objects.filter(id=employee_id).first()

        return context