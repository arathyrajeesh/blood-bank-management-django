from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Donor, Patient
from .forms import RegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test


def home(request):
    return render(request,'index.html')
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
                required_units = form.cleaned_data['required_units'] or 1
                Patient.objects.create(user=user, phone=phone, gender=gender,
                                        blood_group=blood_group, address=address, required_units=required_units)

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
    return render(request, 'donor/donor_login.html')


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

@login_required
def donor_dashboard(request):
    donor = Donor.objects.get(user=request.user)
    return render(request, 'donor/donor_dashboard.html', {'donor': donor})


@login_required
def patient_dashboard(request):
    patient = Patient.objects.get(user=request.user)
    return render(request, 'patient/patient_dashboard.html', {'patient': patient})

def logout_view(request):
    logout(request)
    return redirect('main')


def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    donors = Donor.objects.all()
    patients = Patient.objects.all()
    total_donors = donors.count()
    total_patients = patients.count()
    available_donors = donors.filter(available=True).count()

    return render(request, 'admin/admin_dashboard.html', {
        'donors': donors,
        'patients': patients,
        'total_donors': total_donors,
        'total_patients': total_patients,
        'available_donors': available_donors,
    })