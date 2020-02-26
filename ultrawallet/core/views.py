from decimal import Decimal, InvalidOperation, getcontext, ROUND_HALF_UP, ROUND_HALF_DOWN
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
        from_person_id = int(request.POST['from-person'])
        from_person = list(filter(lambda x: x.user_id == from_person_id, persons))[0]

        to_persons = Person.objects.filter(inn__in=inn_set)

        # todo detect wrong INN
        to_persons_inn_list = [person.inn for person in to_persons]
        for typed_inn in inn_set:
            if typed_inn not in to_persons_inn_list:
                error_messages.append('{} is unattached INN'.format(typed_inn))
        if error_messages:
            return render(request, 'transfers/to_many.html', {
                'persons': persons,
                'error_message': '\n'.join(error_messages)
            })
        else:
            to_persons_list = list(filter(lambda x: x.inn in inn_set, persons))

        # todo check money
        if from_person.account < amount:
            return render(request, 'transfers/to_many.html', {
                'persons': persons,
                'error_message': 'Not enough money'
            })

        # todo test money with '2e10'
        # todo transfer with a transaction
        money_context = getcontext()
        money_context.prec = 3
        money_context.rounding = ROUND_HALF_DOWN

        credit_for_each = amount / len(inn_set)
        debit = credit_for_each * len(inn_set)
        from_person.account -= debit
        import pudb; pu.db
        from_person.save()
        for lucky in to_persons_list:
            lucky.account += credit_for_each
            lucky.save()

    return render(request, 'transfers/to_many.html', {
        'persons': persons,
        'error_message': error_message
    })
