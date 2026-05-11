import logging
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date

logger = logging.getLogger(__name__)

def validate_age(birth_date):
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if age < 18:
        logger.warning(f"Validation failed: User age is {age}, which is under 18.")
        raise ValidationError("Age must be 18 or older.")


phone_regex = RegexValidator(
    regex=r'^\+375 \(29\) \d{3}-\d{2}-\d{2}$',
    message="Format: +375 (29) XXX-XX-XX"
)


class Specialization(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    service_types = models.ManyToManyField('cleaning.ServiceType', related_name='specializations')

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"Specialization '{self.name}' {'created' if is_new else 'updated'} (ID: {self.id})")

    def __str__(self):
        return self.name


class Client(models.Model):
    class ClientType(models.TextChoices):
        INDIVIDUAL = 'individual', 'Private Individual'
        LEGAL = 'legal', 'Legal Entity'

    client_type = models.CharField(
        max_length=20,
        choices=ClientType.choices,
        default=ClientType.INDIVIDUAL
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="patronymic")
    company_name = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(validators=[phone_regex], max_length=20)
    birth_date = models.DateField(validators=[validate_age])

    def clean(self):
        if self.client_type == self.ClientType.LEGAL and not self.company_name:
            logger.error(f"Client validation error: Company name missing for legal entity (User: {self.user.username})")
            raise ValidationError({
                'company_name': "Company name is required for legal entities."
            })

        if self.client_type == self.ClientType.INDIVIDUAL and self.company_name:
            logger.error(f"Client validation error: Company name provided for individual (User: {self.user.username})")
            raise ValidationError({
                'company_name': "Company name must be empty for private individuals."
            })

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"Client profile {self.user.username} {'created' if is_new else 'updated'} (Type: {self.client_type})")

    def __str__(self):
        name_parts = [self.user.last_name, self.user.first_name, self.patronymic]
        full_name = " ".join([part for part in name_parts if part]).strip()
        return full_name or self.user.username


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="patronymic")
    specializations = models.ManyToManyField(Specialization, related_name='employees')

    photo = models.ImageField(upload_to='employees/', blank=True)
    work_description = models.TextField()
    phone = models.CharField(validators=[phone_regex], max_length=20)
    email = models.EmailField()
    birth_date = models.DateField(validators=[validate_age])

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"Employee profile {self.user.username} {'created' if is_new else 'updated'} (ID: {self.id})")

    def __str__(self):
        name_parts = [self.user.last_name, self.user.first_name, self.patronymic]
        full_name = " ".join([part for part in name_parts if part]).strip()
        return full_name or self.user.username