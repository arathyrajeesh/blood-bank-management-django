from django import forms
from django.contrib.auth.models import User
from .models import Donor, Patient, BLOOD_GROUP_CHOICES, GENDER_CHOICES

ROLE_CHOICES = [
    ('donor', 'Donor'),
    ('patient', 'Patient'),
]

class RegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    phone = forms.CharField(max_length=15)
    gender = forms.ChoiceField(choices=GENDER_CHOICES)
    blood_group = forms.ChoiceField(choices=BLOOD_GROUP_CHOICES)
    address = forms.CharField(widget=forms.Textarea)
    age = forms.IntegerField(required=False)
    required_units = forms.IntegerField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
