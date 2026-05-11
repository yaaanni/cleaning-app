import pytest
from content.models import PromoCode
from content.services import get_categorized_promo_codes


@pytest.mark.django_db
class TestContentServices:

    def test_get_categorized_promo_codes_filtering(self):
        PromoCode.objects.create(code="ACTIVE_1", discount_percent=10, is_archived=False)
        PromoCode.objects.create(code="ACTIVE_2", discount_percent=20, is_archived=False)
        PromoCode.objects.create(code="OLD_CODE", discount_percent=5, is_archived=True)

        result = get_categorized_promo_codes()

        assert result['active_promos'].count() == 2
        assert result['archived_promos'].count() == 1

        assert result['archived_promos'][0].code == "OLD_CODE"

    def test_get_categorized_promo_codes_sorting(self):
        PromoCode.objects.create(code="MID", discount_percent=15, is_archived=False)
        PromoCode.objects.create(code="LOW", discount_percent=5, is_archived=False)
        PromoCode.objects.create(code="HIGH", discount_percent=30, is_archived=False)

        result = get_categorized_promo_codes()
        active = result['active_promos']

        assert active[0].code == "HIGH"
        assert active[1].code == "MID"
        assert active[2].code == "LOW"

    def test_get_categorized_promo_codes_empty(self):
        result = get_categorized_promo_codes()

        assert result['active_promos'].count() == 0
        assert result['archived_promos'].count() == 0

    def test_get_categorized_promo_codes_only_archived(self):
        PromoCode.objects.create(code="ARCH_1", discount_percent=10, is_archived=True)

        result = get_categorized_promo_codes()

        assert result['active_promos'].count() == 0
        assert result['archived_promos'].count() == 1