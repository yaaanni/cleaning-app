import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from users.models import Specialization, Client, Employee, validate_age


@pytest.fixture
def test_user():
    return User.objects.create(username="testuser", first_name="John", last_name="Doe")


@pytest.fixture
def valid_birth_date():
    return date.today() - timedelta(days=25 * 365)


@pytest.fixture
def invalid_birth_date():
    return date.today() - timedelta(days=15 * 365)


class TestValidators:

    def test_validate_age_valid(self, valid_birth_date):
        validate_age(valid_birth_date)

    def test_validate_age_invalid(self, invalid_birth_date):
        with pytest.raises(ValidationError, match="Age must be 18 or older."):
            validate_age(invalid_birth_date)


@pytest.mark.django_db
class TestUsersModels:

    def test_specialization_str(self):
        spec = Specialization.objects.create(name="Plumber", description="Fixes pipes")
        assert str(spec) == "Plumber"

    def test_client_str_with_full_name(self, test_user, valid_birth_date):
        client = Client.objects.create(
            user=test_user,
            patronymic="Smith",
            phone="+375 (29) 123-45-67",
            birth_date=valid_birth_date,
            client_type=Client.ClientType.INDIVIDUAL
        )
        assert str(client) == "Doe John Smith"

    def test_client_str_fallback_to_username(self, valid_birth_date):
        user_no_name = User.objects.create(username="anon_user")
        client = Client.objects.create(
            user=user_no_name,
            phone="+375 (29) 123-45-67",
            birth_date=valid_birth_date,
            client_type=Client.ClientType.INDIVIDUAL
        )
        assert str(client) == "anon_user"

    def test_client_clean_legal_entity_valid(self, test_user, valid_birth_date):
        client = Client(
            user=test_user,
            phone="+375 (29) 123-45-67",
            birth_date=valid_birth_date,
            client_type=Client.ClientType.LEGAL,
            company_name="OOO Test"
        )
        client.clean()

    def test_client_clean_legal_entity_invalid_missing_company(self, test_user, valid_birth_date):
        client = Client(
            user=test_user,
            phone="+375 (29) 123-45-67",
            birth_date=valid_birth_date,
            client_type=Client.ClientType.LEGAL,
            company_name=""
        )
        with pytest.raises(ValidationError) as excinfo:
            client.clean()
        assert 'company_name' in excinfo.value.error_dict

    def test_client_clean_individual_invalid_has_company(self, test_user, valid_birth_date):
        client = Client(
            user=test_user,
            phone="+375 (29) 123-45-67",
            birth_date=valid_birth_date,
            client_type=Client.ClientType.INDIVIDUAL,
            company_name="OOO Test"
        )
        with pytest.raises(ValidationError) as excinfo:
            client.clean()
        assert 'company_name' in excinfo.value.error_dict

    def test_employee_str_and_specializations(self, test_user, valid_birth_date):
        spec = Specialization.objects.create(name="Cleaner", description="...")
        employee = Employee.objects.create(
            user=test_user,
            patronymic="Ivanovich",
            phone="+375 (29) 999-88-77",
            email="test@test.com",
            birth_date=valid_birth_date,
            work_description="Excellent worker"
        )
        employee.specializations.add(spec)

        assert str(employee) == "Doe John Ivanovich"
        assert employee.specializations.count() == 1
        assert employee.specializations.first().name == "Cleaner"