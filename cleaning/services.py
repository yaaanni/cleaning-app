import logging
import base64
import io
import urllib
import matplotlib
import requests
import statistics
from datetime import date
from .models import Order, OrderItem

matplotlib.use('Agg')
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def get_weather_api():
    try:
        logger.info("Fetching weather data for Minsk")
        url = "https://api.open-meteo.com/v1/forecast?latitude=53.9&longitude=27.56&current_weather=true"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        temp = data.get('current_weather', {}).get('temperature')
        logger.info(f"Weather data retrieved successfully: {temp}°C")
        return temp
    except Exception:
        logger.error("Failed to retrieve weather data", exc_info=True)
        return None


def get_exchange_rate_api():
    try:
        logger.info("Fetching BYN to USD exchange rate")
        url = "https://api.exchangerate-api.com/v4/latest/BYN"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        rate = data.get('rates', {}).get('USD')
        logger.info(f"Exchange rate retrieved: {rate}")
        return rate
    except Exception:
        logger.error("Failed to retrieve exchange rate", exc_info=True)
        return None


def get_sales_statistics():
    logger.info("Starting sales statistics calculation")
    paid_orders = Order.objects.filter(status=Order.Status.PAID)
    sales = [order.get_total_cost() for order in paid_orders]

    total_sales = sum(sales)
    mean_sales = statistics.mean(sales) if sales else 0
    median_sales = statistics.median(sales) if sales else 0

    try:
        mode_sales = statistics.mode(sales) if sales else 0
    except statistics.StatisticsError:
        logger.warning("Multiple modes found in sales data")
        mode_sales = "Multiple modes"

    clients = {order.client for order in paid_orders}
    today = date.today()
    ages = [
        today.year - c.birth_date.year - ((today.month, today.day) < (c.birth_date.month, c.birth_date.day))
        for c in clients
    ]
    mean_age = statistics.mean(ages) if ages else 0
    median_age = statistics.median(ages) if ages else 0

    logger.info(f"Statistics calculated for {len(sales)} orders and {len(clients)} clients")
    return {
        'total_sales': total_sales,
        'mean_sales': round(mean_sales, 2),
        'median_sales': round(median_sales, 2),
        'mode_sales': mode_sales,
        'mean_age': round(mean_age, 1),
        'median_age': round(median_age, 1),
    }


def get_popular_profitable_services():
    logger.info("Analyzing popular and profitable services")
    items = OrderItem.objects.filter(order__status=Order.Status.PAID)

    stats = {}
    for item in items:
        st_name = item.service.service_type.name
        if st_name not in stats:
            stats[st_name] = {'quantity': 0, 'revenue': 0}
        stats[st_name]['quantity'] += item.quantity
        stats[st_name]['revenue'] += item.get_cost()

    if not stats:
        logger.info("No sales data available for service analysis")
        return None, None, []

    most_popular = max(stats.items(), key=lambda x: x[1]['quantity'])[0]
    most_profitable = max(stats.items(), key=lambda x: x[1]['revenue'])[0]

    chart_labels = list(stats.keys())
    chart_data = [float(data['revenue']) for data in stats.values()]

    logger.info(f"Analysis complete. Popular: {most_popular}, Profitable: {most_profitable}")
    return most_popular, most_profitable, {'labels': chart_labels, 'data': chart_data}


def get_matplotlib_chart():
    logger.info("Generating profit distribution chart with Matplotlib")
    items = OrderItem.objects.filter(order__status=Order.Status.PAID)

    stats = {}
    for item in items:
        st_name = item.service.service_type.name
        stats[st_name] = stats.get(st_name, 0) + float(item.get_cost())

    if not stats:
        logger.warning("Chart generation skipped: No sales data available")
        return None

    labels = list(stats.keys())
    values = list(stats.values())

    plt.figure(figsize=(8, 4))
    plt.bar(labels, values, color='#3498db', edgecolor='#2980b9')
    plt.title('Revenue by Category (BYN)', fontsize=14)
    plt.xlabel('Service Category', fontsize=12)
    plt.ylabel('Total Revenue', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)

    plt.close()
    logger.info("Matplotlib chart successfully generated and encoded to base64")

    return uri