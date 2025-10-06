from django import forms 
from django.contrib.auth.models import User
from .models import Donor, Patient, BloodStock, BLOOD_GROUP_CHOICES, GENDER_CHOICES

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
    age = forms.IntegerField(required=False, label="Age (Donor only)")
    required_units = forms.IntegerField(required=False, label="Required Units (Patient only)")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        age = cleaned_data.get('age')
        required_units = cleaned_data.get('required_units')

        if role == 'donor' and not age:
            self.add_error('age', 'Donor must provide age.')
        

        return cleaned_data


class BloodStockForm(forms.ModelForm):
    class Meta:
        model = BloodStock
        fields = ['blood_group', 'units']


class LastDonationForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ['last_donation_date']
        widgets = {
            'last_donation_date': forms.DateInput(attrs={'type': 'date'})
        }