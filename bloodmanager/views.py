from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from datetime import date, timedelta 
from .models import Donor, Patient, BloodStock, Hospital
from .forms import RegistrationForm, BloodStockForm, LastDonationForm,HospitalRegistrationForm



def home(request):
    stock = BloodStock.objects.all()
    return render(request, 'index.html', {'stock': stock})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            phone = form.cleaned_data['phone']
            gender = form.cleaned_data['gender']
            blood_group = form.cleaned_data['blood_group']
            address = form.cleaned_data['address']

            user = User.objects.create_user(username=username, email=email, password=password)

            if role == 'donor':
                age = form.cleaned_data['age']
                Donor.objects.create(user=user, phone=phone, gender=gender,
                                        blood_group=blood_group, address=address, age=age)
            elif role == 'patient':
                required_units = form.cleaned_data.get('required_units') or 1
                Patient.objects.create(user=user, phone=phone, gender=gender,
                                        blood_group=blood_group, address=address, required_units=required_units)
            elif role == 'hospital':
                name = form.cleaned_data['name']
                Hospital.objects.create(user=user, name=name, phone=phone, address=address)

            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('main')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


def donor_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            if Donor.objects.filter(user=user).exists():
                login(request, user)
                return redirect('donor-dashboard')
            messages.error(request, 'Not registered as a donor.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'donor_login.html')


def patient_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            if Patient.objects.filter(user=user).exists():
                login(request, user)
                return redirect('patient-dashboard')
            messages.error(request, 'Not registered as a patient.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'patient_login.html')


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user and user.is_superuser:
            login(request, user)
            return redirect('admin-dashboard')
        else:
            messages.error(request, "Invalid admin credentials.")
    return render(request, 'admin_login.html')

def hospital_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            if Hospital.objects.filter(user=user).exists():
                login(request, user)
                return redirect('hospital-dashboard')
            messages.error(request, 'Not registered as a hospital.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'hospital/hospital_login.html')
def hospital_register(request):
    if request.method == 'POST':
        form = HospitalRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']
            address = form.cleaned_data['address']

            user = User.objects.create_user(username=username, email=email, password=password)
            Hospital.objects.create(user=user, name=name, phone=phone, address=address)

            messages.success(request, 'Hospital registration successful! You can now log in.')
            return redirect('hospital-login')
    else:
        form = HospitalRegistrationForm()
    
    return render(request, 'hospital/hospital_register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('main')


@login_required
def hospital_dashboard(request):
    hospital = Hospital.objects.get(user=request.user)
    stock = BloodStock.objects.all().order_by('blood_group')

    return render(request, 'hospital/hospital_dashboard.html', {
        'hospital': hospital,
        'stock': stock,
    })

@login_required
def donor_dashboard(request):
    donor = Donor.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = LastDonationForm(request.POST, instance=donor)
        if form.is_valid():
            new_date = form.cleaned_data['last_donation_date']
            
            if new_date and (new_date == date.today() or new_date > (date.today() - timedelta(days=7))): 
                try:
                    stock_item, created = BloodStock.objects.get_or_create(blood_group=donor.blood_group)
                    stock_item.units += 1 
                    stock_item.save()
                except Exception as e:
                    messages.warning(request, f'Stock update failed: {e}')

            form.save()
            messages.success(request, 'Last donation date updated successfully! Availability recalculated.')
            return redirect('donor-dashboard')
    else:
        form = LastDonationForm(instance=donor)
        
    return render(request, 'donor/donor_dashboard.html', {'donor': donor, 'form': form})



@login_required
def patient_dashboard(request):
    patient = Patient.objects.get(user=request.user)
    return render(request, 'patient/patient_dashboard.html', {'patient': patient})


@login_required
def search_donors(request):
    patient = Patient.objects.get(user=request.user)
    required_blood_group = patient.blood_group
    
    compatible_groups = {
        'A+': ['A+', 'A-', 'O+', 'O-'],
        'A-': ['A-', 'O-'],
        'B+': ['B+', 'B-', 'O+', 'O-'],
        'B-': ['B-', 'O-'],
        'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'], 
        'AB-': ['AB-', 'A-', 'B-', 'O-'],
        'O+': ['O+', 'O-'],
        'O-': ['O-'], 
    }.get(required_blood_group, [])

    exact_match_donors = Donor.objects.filter(
        blood_group=required_blood_group, 
        available=True
    ).select_related('user')
    
    compatible_donors = Donor.objects.filter(
        blood_group__in=compatible_groups,
        available=True
    ).exclude(blood_group=required_blood_group).select_related('user') 

    context = {
        'patient': patient,
        'required_blood_group': required_blood_group,
        'exact_match_donors': exact_match_donors,
        'compatible_donors': compatible_donors,
        'compatible_groups': compatible_groups,
    }
    
    return render(request, 'patient/search_donors.html', context)



def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    donors = Donor.objects.all()
    patients = Patient.objects.all()
    stock = BloodStock.objects.all().order_by('blood_group') 

    total_donors = donors.count()
    available_donors = donors.filter(available=True).count()
    total_patients = patients.count()
    total_stock_units = sum(item.units for item in stock)

    stock_form = None
    if request.method == 'POST':
        stock_form = BloodStockForm(request.POST)
        if stock_form.is_valid():
            blood_group = stock_form.cleaned_data['blood_group']
            units = stock_form.cleaned_data['units']
            
            stock_item, created = BloodStock.objects.get_or_create(blood_group=blood_group, defaults={'units': 0})
            stock_item.units = units
            stock_item.save()
            messages.success(request, f'Blood Stock for {blood_group} updated successfully to {units} units.')
            return redirect('admin-dashboard')
    else:
        stock_form = BloodStockForm()

    return render(request, 'admin/admin_dashboard.html', {
        'donors': donors,
        'patients': patients,
        'stock': stock,
        'total_donors': total_donors,
        'total_patients': total_patients,
        'available_donors': available_donors,
        'total_stock_units': total_stock_units,
        'stock_form': stock_form,
    })