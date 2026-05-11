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