import logging
from .models import PromoCode

logger = logging.getLogger(__name__)


def get_categorized_promo_codes():
    logger.info("Fetching and categorizing promo codes")

    active_promos = PromoCode.objects.filter(is_archived=False).order_by('-discount_percent')
    archived_promos = PromoCode.objects.filter(is_archived=True).order_by('-discount_percent')

    logger.info(
        f"Successfully categorized {active_promos.count()} active and {archived_promos.count()} archived promo codes")

    return {
        'active_promos': active_promos,
        'archived_promos': archived_promos
    }

import matplotlib.pyplot as plt
import io
import base64


def get_matplotlib_chart(labels, values):
    import matplotlib
    matplotlib.use('Agg')

    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color='#4361ee')
    plt.title('Top 5 Selling Services')
    plt.ylabel('Units Sold')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close()

    return f"data:image/png;base64,{image_base64}"