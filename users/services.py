import logging
import calendar
import statistics
import requests
from django.utils import timezone
from cleaning.models import Order

logger = logging.getLogger(__name__)

def get_client_orders(client, search_query='', sort_by='-date_created'):
    logger.info(f"Fetching orders for client: {client.user.username} (Search: '{search_query}', Sort: {sort_by})")
    orders = Order.objects.filter(client=client)

    if search_query:
        orders = orders.filter(address__icontains=search_query)

    orders = orders.order_by(sort_by)
    return orders


def get_client_statistics(orders):
    logger.info("Calculating financial statistics for client")
    paid_orders = [order for order in orders if order.status == 'paid']
    costs = [float(order.get_total_cost()) for order in paid_orders]

    if not costs:
        logger.warning("No paid orders found for statistics calculation")
        return {
            'total_spent': 0,
            'mean_spent': 0,
            'median_spent': 0,
            'mode_spent': 0
        }

    try:
        mode_val = statistics.mode(costs)
    except statistics.StatisticsError:
        logger.info("Multiple modes or no mode found in order costs")
        mode_val = "N/A (No exact mode)"

    stats = {
        'total_spent': sum(costs),
        'mean_spent': round(statistics.mean(costs), 2),
        'median_spent': round(statistics.median(costs), 2),
        'mode_spent': mode_val
    }
    logger.info(f"Statistics calculated: Total Spent = {stats['total_spent']}")
    return stats


def get_client_datetime_info(user):
    logger.info(f"Generating datetime and calendar info for user: {user.username}")
    now_local = timezone.localtime()
    now_utc = timezone.now()
    date_joined_local = timezone.localtime(user.date_joined)

    text_cal = calendar.TextCalendar(calendar.MONDAY)
    calendar_str = text_cal.formatmonth(now_local.year, now_local.month)

    return {
        'current_timezone': timezone.get_current_timezone_name(),
        'date_local': now_local.strftime("%d/%m/%Y %H:%M"),
        'date_utc': now_utc.strftime("%d/%m/%Y %H:%M"),
        'joined_local': date_joined_local.strftime("%d/%m/%Y %H:%M"),
        'joined_utc': user.date_joined.strftime("%d/%m/%Y %H:%M"),
        'text_calendar': calendar_str
    }


def get_external_apis_data():
    api_data = {}

    try:
        logger.info("Requesting weather data from Open-Meteo API")
        weather_url = "https://api.open-meteo.com/v1/forecast?latitude=53.9&longitude=27.56&current_weather=true"
        w_res = requests.get(weather_url, timeout=3)
        w_res.raise_for_status()
        w_data = w_res.json()
        api_data['weather'] = f"{w_data['current_weather']['temperature']}°C in Minsk"
    except Exception:
        logger.error("External Weather API call failed", exc_info=True)
        api_data['weather'] = "Weather data unavailable"

    try:
        logger.info("Requesting random advice from AdviceSlip API")
        advice_url = "https://api.adviceslip.com/advice"
        a_res = requests.get(advice_url, timeout=3)
        a_res.raise_for_status()
        a_data = a_res.json()
        api_data['advice'] = a_data['slip']['advice']
    except Exception:
        logger.error("External Advice API call failed", exc_info=True)
        api_data['advice'] = "Keep your home clean and your mind clear!"

    return api_data