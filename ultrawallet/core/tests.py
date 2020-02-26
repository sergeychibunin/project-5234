from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Person


class TransferToManyViewTests(TestCase):

    def setUp(self) -> None:
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
