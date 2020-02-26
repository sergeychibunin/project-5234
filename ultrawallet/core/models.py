from django.db import models
from django.db.models.query import QuerySet
from django.contrib.auth.models import User
from decimal import Decimal, getcontext, ROUND_FLOOR


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    inn = models.IntegerField('INN')
    account = models.DecimalField('Amount of money in RUB', max_digits=14, decimal_places=2)

    def __init__(self, *args, **kwargs):
        super(Person, self).__init__(*args, **kwargs)
        money_context = getcontext()
        money_context.prec = 16
        money_context.rounding = ROUND_FLOOR

    def is_can_pay(self, amount):
        if amount <= 0 or self.account < amount:
            return False
        return True

    @staticmethod
    def transfer2m(from_person: models.Model, amount: int, inn_set: set, persons: QuerySet):
        """Transfer money from one person to many persons by equals parts for each"""
        credit_for_each = Decimal(amount) / len(inn_set)
        debit = credit_for_each * len(inn_set)
        from_person.account -= round_decimal(debit)
        from_person.save()
        for lucky in list(filter(lambda x: x.inn in inn_set, persons)):
            lucky.account += round_decimal(credit_for_each)
            lucky.save()


def round_decimal(dec):
    return dec.quantize(Decimal('0.01'), ROUND_FLOOR)
