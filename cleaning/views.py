import logging
import calendar
from django.utils import timezone
from django.views.generic import TemplateView, ListView
from users.models import Client
from content.models import Vacancy
from .services import (
    get_weather_api,
    get_exchange_rate_api,
    get_sales_statistics,
    get_popular_profitable_services,
    get_matplotlib_chart
)

logger = logging.getLogger(__name__)


class HomeDashboardView(TemplateView):
    template_name = 'cleaning/home.html'

    def get_context_data(self, **kwargs):
        logger.info("Initializing Home Dashboard view context")
        context = super().get_context_data(**kwargs)

        search_query = self.request.GET.get('search', '')
        sort_by = self.request.GET.get('sort', 'user__last_name')

        clients = Client.objects.select_related('user')
        if search_query:
            logger.info(f"Searching clients with query: {search_query}")
            clients = clients.filter(user__last_name__icontains=search_query)

        logger.info(f"Sorting clients by: {sort_by}")
        clients = clients.order_by(sort_by)
        context['clients'] = clients
        context['search_query'] = search_query

        logger.info("Requesting external API data and statistics")
        context['weather'] = get_weather_api()
        context['exchange_rate'] = get_exchange_rate_api()
        context['stats'] = get_sales_statistics()

        pop, prof, chart = get_popular_profitable_services()
        context['most_popular'] = pop
        context['most_profitable'] = prof
        context['matplotlib_chart'] = get_matplotlib_chart()

        logger.info("Calculating system time and calendar data")
        now_local = timezone.localtime()
        now_utc = timezone.now()

        context['current_timezone'] = timezone.get_current_timezone_name()
        context['date_local'] = now_local.strftime("%d/%m/%Y %H:%M:%S")
        context['date_utc'] = now_utc.strftime("%d/%m/%Y %H:%M:%S")

        cal = calendar.TextCalendar(calendar.MONDAY)
        context['text_calendar'] = cal.formatmonth(now_local.year, now_local.month)

        logger.info("Home Dashboard context preparation complete")
        return context


class VacancyListView(ListView):
    """
    Page displaying active job vacancies.
    """
    model = Vacancy
    template_name = 'content/vacancy_list.html'
    context_object_name = 'vacancies'

    def get_queryset(self):
        logger.info("Fetching active vacancies from database")
        queryset = Vacancy.objects.filter(is_active=True)
        logger.info(f"Found {queryset.count()} active vacancies")
        return queryset