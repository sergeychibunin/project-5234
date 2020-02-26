from decimal import Decimal, InvalidOperation
from django.shortcuts import render
from django.db import transaction
from core.models import Person


def parse_inn(inns: str) -> tuple:
    if not inns:
        return set(), 'INN\'s list is empty'
    try:
        inn_set = set([int(inn) for inn in inns.split(' ')])
    except ValueError:
        return set(), 'INN\'s list is wrong'
    return inn_set, ''


def parse_amount(amount: str) -> tuple:
    if not amount:
        return 0, 'Amount is empty'
    try:
        return Decimal(amount), ''
    except InvalidOperation:
        return 0, 'Amount is wrong'


def parse_person(person: str, persons: list) -> tuple:
    try:
        from_person_id = int(person)
        return list(filter(lambda x: x.user_id == from_person_id, persons))[0], ''
    except (IndexError, ValueError):
        return None, 'Person is wrong'


def validate_inns(inns: set) -> list:
    errors = []
    to_persons_inn_list = [person.inn for person in (Person.objects.filter(inn__in=inns))]
    for typed_inn in inns:
        if typed_inn not in to_persons_inn_list:
            errors.append('{} is unattached INN'.format(typed_inn))
    return errors


@transaction.atomic
def transfer2m(request):
    error_message = 'Welcome'
    persons = Person.objects.select_related('user').all()

    if request.method == 'POST':
        error_message = 'Success'
        error_messages = []

        inn_set, _error_message = parse_inn(request.POST['inns'])
        if _error_message:
            error_messages += [_error_message]

        amount, _error_message = parse_amount(request.POST['amount'])
        if _error_message:
            error_messages += [_error_message]

        from_person, _error_message = parse_person(request.POST['from-person'], persons)
        if _error_message:
            error_messages += [_error_message]

        _error_messages = validate_inns(inn_set)
        if _error_messages:
            error_messages += _error_messages

        if error_messages:
            return render(request, 'transfers/to_many.html', {
                'persons': persons,
                'error_message': '\n'.join(error_messages)
            })

        if not from_person.is_can_pay(amount):
            return render(request, 'transfers/to_many.html', {
                'persons': persons,
                'error_message': 'Not enough money'
            })

        Person.transfer2m(from_person, amount, inn_set, persons)

    return render(request, 'transfers/to_many.html', {
        'persons': persons,
        'error_message': error_message
    })
