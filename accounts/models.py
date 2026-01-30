from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Session(models.Model):
    token = models.CharField(max_length=255)
    site = models.CharField(max_length=511)


class Shop(models.Model):
    myshopify_domain = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=255)
    name = models.CharField(max_length=255, null=True)
    currency = models.CharField(max_length=4, null=True)
