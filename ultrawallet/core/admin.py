from django.contrib import admin
from .models import Person


class PersonAdmin(admin.ModelAdmin):
    fields = ['user', 'inn', 'account']


admin.site.register(Person, PersonAdmin)
