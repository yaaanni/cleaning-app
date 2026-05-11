import logging
from django.db import models
from users.models import Client

logger = logging.getLogger(__name__)

class CompanyInfo(models.Model):
    name = models.CharField(max_length=100, default="Cleaning Service")
    description = models.TextField()
    logo = models.ImageField(upload_to='company/', blank=True)
    video_url = models.URLField(blank=True)
    requisites = models.TextField()

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"Company information {'created' if is_new else 'updated'}")

    def __str__(self):
        return self.name


class CompanyHistory(models.Model):
    year = models.IntegerField()
    description = models.TextField()

    class Meta:
        ordering = ['year']

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"History milestone for year {self.year} {'added' if is_new else 'modified'}")

    def __str__(self):
        return str(self.year)


class News(models.Model):
    title = models.CharField(max_length=200)
    short_content = models.CharField(max_length=255)
    full_content = models.TextField()
    image = models.ImageField(upload_to='news/')
    pub_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"News article '{self.title}' {'published' if is_new else 'updated'}")

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"FAQ item {'created' if is_new else 'updated'}: {self.question}")

    def __str__(self):
        return self.question


class Vacancy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"Vacancy '{self.title}' {'posted' if is_new else 'updated'}. Active status: {self.is_active}")

    def __str__(self):
        return self.title


class Review(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"New review submitted by Client ID {self.client.id}. Rating: {self.rating}/5")
        else:
            logger.info(f"Review by Client ID {self.client.id} was modified")

    def __str__(self):
        return f"Review by {self.client} ({self.rating}/5)"


class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField()
    is_archived = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        super().save(*args, **kwargs)
        logger.info(f"PromoCode '{self.code}' (Discount: {self.discount_percent}%) {'created' if is_new else 'updated'}. Archived: {self.is_archived}")

    def __str__(self):
        return self.code