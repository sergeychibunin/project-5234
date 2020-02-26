from decimal import Decimal, getcontext, ROUND_CEILING
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Person, round_decimal
from core.views import parse_inn, parse_amount, parse_person, validate_inns


def fill_db():
    user = User()
    user.username = 'user1'
    user.save()
    person = Person()
    person.user = user
    person.inn = '1'
    person.account = '1'
    person.save()

    user = User()
    user.username = 'user2'
    user.save()
    person = Person()
    person.user = user
    person.inn = '2'
    person.account = '0'
    person.save()

    user = User()
    user.username = 'user22'
    user.save()
    person = Person()
    person.user = user
    person.inn = '123'
    person.account = '50'
    person.save()

    user = User()
    user.username = 'user33'
    user.save()
    person = Person()
    person.user = user
    person.inn = '456'
    person.account = '50'
    person.save()

    user = User()
    user.username = 'user44'
    user.save()
    person = Person()
    person.user = user
    person.inn = '452345134234'
    person.account = '-100'
    person.save()

    user = User()
    user.username = 'user55'
    user.save()
    person = Person()
    person.user = user
    person.inn = '67896'
    person.account = '0.99'
    person.save()


class TransferToManyViewTests(TestCase):

    def setUp(self) -> None:
        fill_db()

    def test_showing_form(self):
        response = self.client.get(reverse('transfer2m'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], 'Welcome')

    def test_showing_error(self):
        response = self.client.post(reverse('transfer2m'), {'inns': '1', 'amount': '100000', 'from-person': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.context['error_message'], 'Welcome')

    def test_transfer(self):
        response = self.client.post(
            reverse('transfer2m'),
            {'inns': '2', 'amount': '1', 'from-person': '1'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], 'Success')
        lucky = Person.objects.get(pk=2)
        self.assertEqual(lucky.account, 1)
        major = Person.objects.get(pk=1)
        self.assertEqual(major.account, 0)

    def test_failure_transfer_inn(self):
        """There is one problem with INN"""
        response = self.client.post(
            reverse('transfer2m'),
            {'inns': '0', 'amount': '1', 'from-person': '1'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], '0 is unattached INN')
        lucky = Person.objects.get(pk=2)
        self.assertEqual(lucky.account, 0)
        major = Person.objects.get(pk=1)
        self.assertEqual(major.account, 1)

    def test_failure_transfer_amount(self):
        """There is one problem with an amount"""
        response = self.client.post(
            reverse('transfer2m'),
            {'inns': '2', 'amount': '', 'from-person': '1'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], 'Amount is empty')
        lucky = Person.objects.get(pk=2)
        self.assertEqual(lucky.account, 0)
        major = Person.objects.get(pk=1)
        self.assertEqual(major.account, 1)

    def test_failure_transfer_from_person(self):
        """There is one problem with a wrong person"""
        response = self.client.post(
            reverse('transfer2m'),
            {'inns': '2', 'amount': '1', 'from-person': '0'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'], 'Person is wrong')
        lucky = Person.objects.get(pk=2)
        self.assertEqual(lucky.account, 0)
        major = Person.objects.get(pk=1)
        self.assertEqual(major.account, 1)

    def test_failure_transfer_complex(self):
        """There are many problems with input data"""
        response = self.client.post(
            reverse('transfer2m'),
            {'inns': '0', 'amount': '1', 'from-person': '0'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_message'],
                         'Person is wrong\n0 is unattached INN')
        lucky = Person.objects.get(pk=2)
        self.assertEqual(lucky.account, 0)
        major = Person.objects.get(pk=1)
        self.assertEqual(major.account, 1)


class TransferProcessingTests(TestCase):

    def setUp(self) -> None:
        fill_db()

    def test_parse_inn(self):
        inns, error_msg = parse_inn(not '1')
        self.assertEqual(inns, set())
        self.assertEqual(error_msg, 'INN\'s list is empty')

        for typo in ('a', 'a 1', '1, 2',
                     '1.2 3', ' 3 4', '1  2'):
            inns, error_msg = parse_inn(typo)
            self.assertEqual(inns, set())
            self.assertEqual(error_msg, 'INN\'s list is wrong')

        inns, error_msg = parse_inn('1 2')
        self.assertEqual(inns, {1, 2})
        self.assertEqual(error_msg, '')

    def test_parse_amount(self):
        amount, error_msg = parse_amount(not '1')
        self.assertEqual(amount, 0)
        self.assertEqual(error_msg, 'Amount is empty')

        for typo in ('a', 'a 1', '1, 2',
                     '1.2 3', ' 3 4', '1  2',
                     ' ', '10a', '4ee2'):
            amount, error_msg = parse_amount(typo)
            self.assertEqual(amount, 0)
            self.assertEqual(error_msg, 'Amount is wrong')

        amount, error_msg = parse_amount('3.50')
        self.assertEqual(amount, Decimal('3.50'))
        self.assertEqual(error_msg, '')

        amount, error_msg = parse_amount('-4e2')
        self.assertEqual(amount, Decimal('-4E+2'))
        self.assertEqual(error_msg, '')

    def test_parse_person(self):
        persons = Person.objects.all()
        for typo in ('a', 'a 1', '1, 2',
                     '1.2 3', '', '1  2 ',
                     ' ', '10a', '4ee2'):
            person, error_msg = parse_person(typo, persons)
            self.assertEqual(person, None)
            self.assertEqual(error_msg, 'Person is wrong')

        person, error_msg = parse_person('1', persons)
        self.assertEqual(person, Person.objects.get(pk=1))
        self.assertEqual(error_msg, '')

    def test_validate_inns(self):
        """Input INNs must be attached to users"""
        errors = validate_inns({1, 3, 4})
        self.assertEqual(errors, ['3 is unattached INN', '4 is unattached INN'])
        errors = validate_inns({1, 2})
        self.assertEqual(errors, [])

    def test_money_context_for_person_processing(self):
        ctx = getcontext()
        ctx.prec = 1
        ctx.rounding = ROUND_CEILING
        self.assertEqual(ctx.prec, 1)
        self.assertEqual(ctx.rounding, ROUND_CEILING)
        _ = Person()
        ctx = getcontext()
        self.assertNotEqual(ctx.prec, 1)
        self.assertNotEqual(ctx.rounding, ROUND_CEILING)

    def test_person_is_can_pay(self):
        person = Person.objects.get(pk=1)
        self.assertEqual(person.is_can_pay(-.000000000000000001), False)
        self.assertEqual(person.is_can_pay(1000000000000000000), False)
        self.assertEqual(person.is_can_pay(2), False)
        self.assertEqual(person.is_can_pay(1), True)

    def test_transfer_to_many_person_from_one(self):
        Person.transfer2m(
            Person.objects.get(pk=3),
            50,
            {456, 452345134234, 67896},
            Person.objects.all()
        )
        self.assertEqual(Person.objects.get(pk=3).account, Decimal('0.01'))
        self.assertEqual(Person.objects.get(pk=4).account, Decimal('66.66'))
        self.assertEqual(Person.objects.get(pk=5).account, Decimal('-83.34'))
        self.assertEqual(Person.objects.get(pk=6).account, Decimal('17.65'))

    def test_rounding(self):
        with self.assertRaises(AttributeError):
            round_decimal('qwe')
            round_decimal('qwe')
        rounded = round_decimal(Decimal('100.5333333333333333333333'))
        self.assertEqual(rounded, Decimal('100.53'))
