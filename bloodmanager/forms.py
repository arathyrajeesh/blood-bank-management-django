from django import forms 
from django.contrib.auth.models import User
from .models import Donor, Patient, BloodStock, BLOOD_GROUP_CHOICES, GENDER_CHOICES,Hospital,DonorHealthCheck

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
    name = forms.CharField(required=False, label="Hospital Name (Hospital only)")
    profile_photo = forms.ImageField(required=False, label="Profile Photo (Donor only)")
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        age = cleaned_data.get('age')
        name = cleaned_data.get('name')
        profile_photo = cleaned_data.get('profile_photo')
        if role == 'donor' and not age:
            self.add_error('age', 'Donor must provide age.')
        elif role == 'hospital' and not name:
            self.add_error('name', 'Hospital must provide a name.')
        elif role == 'donor' and not profile_photo:
            self.add_error('profile_photo', 'Donor must upload a profile photo.')
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
        fields = ['name', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-field'}),
            'email': forms.EmailInput(attrs={'class': 'input-field'}),
            'phone': forms.TextInput(attrs={'class': 'input-field'}),
        }     


class DonorHealthCheckForm(forms.ModelForm):
    class Meta:
        model = DonorHealthCheck
        fields = [
            'age', 
            'weight', 
            'hemoglobin_level', 
            'has_disease', 
            'recent_medications', 
            'recent_surgeries', 
            'tattoos_or_piercings', 
            'travel_history', 
            'symptoms'
        ]
        widgets = {
            'age': forms.NumberInput(attrs={'min': 18, 'max': 65}),
            'weight': forms.NumberInput(attrs={'min': 45, 'step': 1}),
            'hemoglobin_level': forms.NumberInput(attrs={'step': 0.1}),
            'has_disease': forms.CheckboxInput(),
            'recent_medications': forms.Textarea(attrs={'rows': 2}),
            'recent_surgeries': forms.Textarea(attrs={'rows': 2}),
            'tattoos_or_piercings': forms.Textarea(attrs={'rows': 2}),
            'travel_history': forms.Textarea(attrs={'rows': 2}),
            'symptoms': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'has_disease': 'Do you have any chronic or infectious diseases?',
            'recent_medications': 'Recent Medications',
            'recent_surgeries': 'Recent Surgeries',
            'tattoos_or_piercings': 'Recent Tattoos or Piercings (last 12 months)',
            'travel_history': 'Recent Travel History (last 6 months)',
            'symptoms': 'Any recent symptoms like fever, cold, etc.'
        }
class PatientRequestForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['blood_group', 'required_units', 'address', 'phone']
        widgets = {
            'blood_group': forms.Select(choices=BLOOD_GROUP_CHOICES, attrs={'class': 'form-control'}),
            'required_units': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
        
class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ['profile_photo', 'phone', 'address', 'blood_group', 'age', 'gender']
        widgets = {
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'blood_group': forms.Select(choices=BLOOD_GROUP_CHOICES, attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(choices=GENDER_CHOICES, attrs={'class': 'form-control'}),
        }