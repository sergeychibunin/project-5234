from django.db import models
from django.contrib.auth.models import User


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    inn = models.IntegerField('INN')
    account = models.DecimalField('Amount of money in RUB', max_digits=14, decimal_places=2)
