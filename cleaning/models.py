import logging
from django.db import models
from users.models import Employee, Client

logger = logging.getLogger(__name__)


class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"ServiceType {'created' if is_new else 'updated'}: {self.name}")

    def __str__(self):
        return self.name


class Service(models.Model):
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"Service {'created' if is_new else 'updated'}: {self.name} (Price: {self.price})")

    def __str__(self):
        return self.name


class Order(models.Model):
    promo_code = models.ForeignKey(
        'content.PromoCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Promo Code"
    )

    class Status(models.TextChoices):
        NEW = 'new', 'New'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    address = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    date_execution = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )

    def get_total_cost(self):
        base_total = sum(item.get_cost() for item in self.items.all())

        if self.promo_code and not self.promo_code.is_archived:
            discount = (base_total * self.promo_code.discount_percent) / 100
            final_total = base_total - discount
            result = round(final_total, 2)
        else:
            result = round(base_total, 2)

        logger.info(f"Total cost calculated for Order #{self.id}: {result} BYN (Promo: {self.promo_code})")
        return result

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(
            f"Order #{self.id} {'created' if is_new else 'updated'}. Status: {self.status}, Client: {self.client}")

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Frozen price at the time of order")

    def save(self, *args, **kwargs):
        if not self.id:
            self.price = self.service.price
            logger.info(f"Price frozen for OrderItem: {self.service.name} at {self.price} BYN")
        super().save(*args, **kwargs)

    def get_cost(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.service.name} (Order #{self.order.id})"