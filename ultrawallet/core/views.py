from django.shortcuts import render
from core.models import Person


def transfer2m(request):
    persons = Person.objects.select_related('user').all()
    # todo form
    return render(request, 'transfers/to_many.html', {
        'persons': persons
    })
