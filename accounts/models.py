from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Shop(models.Model):
    myshopify_domain = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=255)
    name = models.CharField(max_length=255, null=True)
    currency = models.CharField(max_length=4, null=True)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    is_authentified = models.BooleanField(default=False)
    
    # Settings fields
    pricing_config_enabled = models.BooleanField(default=False)
    auto_sync_enabled = models.BooleanField(default=False)
    sync_frequency = models.CharField(
        max_length=20,
        choices=[
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('manual', 'Manual'),
        ],
        default='daily'
    )

class Session(models.Model):
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='session')
    token = models.CharField(max_length=255)
    site = models.CharField(max_length=511)
