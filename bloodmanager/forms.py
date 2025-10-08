from django import forms 
from django.contrib.auth.models import User
from .models import Donor, Patient, BloodStock, BLOOD_GROUP_CHOICES, GENDER_CHOICES,Hospital

ROLE_CHOICES = [
    ('donor', 'Donor'),
    ('patient', 'Patient'),
    ('hospital', 'Hospital'),
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
    name = forms.CharField(required=False, label="Hospital Name (Hospital only)")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        age = cleaned_data.get('age')
        name = cleaned_data.get('name')

        if role == 'donor' and not age:
            self.add_error('age', 'Donor must provide age.')
        elif role == 'hospital' and not name:
            self.add_error('name', 'Hospital must provide a name.')

        return cleaned_data

class HospitalRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    name = forms.CharField(max_length=255, label="Hospital Name")
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Hospital name is required.")
        return name

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
        
        
class HospitalProfileForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ['name', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }        
