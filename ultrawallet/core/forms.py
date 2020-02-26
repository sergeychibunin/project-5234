from django import forms


class PersonForm(forms.Form):  # todo remove
    user = forms.ChoiceField(label='Your name', max_length=100)