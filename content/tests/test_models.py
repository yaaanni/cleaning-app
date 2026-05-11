import pytest
from django.contrib.auth.models import User
from users.models import Client
from content.models import (
    CompanyInfo, CompanyHistory, News, FAQ, Vacancy, Review, PromoCode
)


@pytest.fixture
def test_user():
    return User.objects.create(username="reviewer", last_name="Smith", first_name="John")


@pytest.fixture
def test_client(test_user):
    return Client.objects.create(
        user=test_user,
        phone="+375 (29) 555-55-55",
        birth_date="1995-10-10"
    )


@pytest.mark.django_db
class TestContentModels:

    def test_company_info_str(self):
        company = CompanyInfo.objects.create(
            name="Super Clean",
            description="Best service",
            requisites="VAT 12345"
        )
        assert str(company) == "Super Clean"

    def test_company_history_str_and_ordering(self):
        h2025 = CompanyHistory.objects.create(year=2025, description="Future")
        h2020 = CompanyHistory.objects.create(year=2020, description="Start")

        assert str(h2020) == "2020"
        histories = CompanyHistory.objects.all()
        assert histories[0].year == 2020
        assert histories[1].year == 2025

    def test_news_str(self):
        news = News.objects.create(
            title="Winter Discount",
            short_content="Save money",
            full_content="Long text about discounts",
            image="news/test.jpg"
        )
        assert str(news) == "Winter Discount"

    def test_faq_str(self):
        faq = FAQ.objects.create(question="How to pay?", answer="By card")
        assert str(faq) == "How to pay?"

    def test_vacancy_str_and_status(self):
        vacancy = Vacancy.objects.create(title="Driver", description="Drive car", is_active=True)
        assert str(vacancy) == "Driver"
        assert vacancy.is_active is True

    def test_review_str_and_rating(self, test_client):
        review = Review.objects.create(
            client=test_client,
            rating=5,
            text="Excellent work!"
        )
        assert str(review) == f"Review by Smith John (5/5)"
        assert review.rating == 5

    def test_promo_code_str_and_discount(self):
        promo = PromoCode.objects.create(code="CLEAN2026", discount_percent=15)
        assert str(promo) == "CLEAN2026"
        assert promo.discount_percent == 15
        assert promo.is_archived is False