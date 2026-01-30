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

class Session(models.Model):
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='session')
    token = models.CharField(max_length=255)
    site = models.CharField(max_length=511)
