from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date
from django.db.models import Sum
from .models import (
    Donor, Patient, BloodStock, Hospital,
    DonorHealthCheck, Donation
)
from .forms import (
    RegistrationForm, BloodStockForm, LastDonationForm,
    HospitalRegistrationForm, HospitalProfileForm,
    DonorHealthCheckForm, PatientRequestForm
)


def home(request):
    stock = BloodStock.objects.values('blood_group').annotate(units=Sum('units')).order_by('blood_group')
    return render(request, 'index.html', {'stock': stock})

def help(request):
    return render(request,'Help.html')
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
                Donor.objects.create(
                    user=user, phone=phone, gender=gender,
                    blood_group=blood_group, address=address, age=age
                )
            elif role == 'patient':
                required_units = form.cleaned_data.get('required_units') or 1
                Patient.objects.create(
                    user=user, phone=phone, gender=gender,
                    blood_group=blood_group, address=address,
                    required_units=required_units
                )
            elif role == 'hospital':
                name = form.cleaned_data['name']
                Hospital.objects.create(
                    user=user, name=name, phone=phone, address=address
                )

            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('main')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

def universal_login(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Donor
            if role == 'donor' and Donor.objects.filter(user=user).exists():
                login(request, user)
                return redirect('donor-dashboard')

            # Patient
            elif role == 'patient' and Patient.objects.filter(user=user).exists():
                login(request, user)
                return redirect('patient-dashboard')

            # Hospital
            elif role == 'hospital' and Hospital.objects.filter(user=user).exists():
                login(request, user)
                return redirect('hospital-dashboard')

            # Admin
            elif role == 'admin' and user.is_superuser:
                login(request, user)
                return redirect('admin-dashboard')

            else:
                messages.error(request, f"You are not registered as a {role}.")
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html')

# def donor_login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         if user and Donor.objects.filter(user=user).exists():
#             login(request, user)
#             return redirect('donor-dashboard')
#         messages.error(request, 'Invalid credentials or not registered as a donor.')
#     return render(request, 'donor_login.html')


# def patient_login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         if user and Patient.objects.filter(user=user).exists():
#             login(request, user)
#             return redirect('patient-dashboard')
#         messages.error(request, 'Invalid credentials or not registered as a patient.')
#     return render(request, 'patient_login.html')


# def hospital_login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         if user and Hospital.objects.filter(user=user).exists():
#             login(request, user)
#             return redirect('hospital-dashboard')
#         messages.error(request, 'Invalid credentials or not registered as a hospital.')
#     return render(request, 'hospital/hospital_login.html')


# def admin_login(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")
#         user = authenticate(username=username, password=password)
#         if user and user.is_superuser:
#             login(request, user)
#             return redirect('admin-dashboard')
#         messages.error(request, "Invalid admin credentials.")
#     return render(request, 'admin_login.html')


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
    hospital = request.user.hospital
    stock = BloodStock.objects.filter(hospital=hospital)

    if request.method == 'POST' and 'add_stock' in request.POST:
        blood_group = request.POST.get('blood_group')
        units = int(request.POST.get('units', 0))

        if blood_group and units > 0:
            obj, created = BloodStock.objects.get_or_create(
                hospital=hospital,
                blood_group=blood_group,
                defaults={'units': units}
            )
            if not created:
                obj.units += units
                obj.save()
            messages.success(request, f"{units} units of {blood_group} added/updated successfully!")
            return redirect('hospital-dashboard')
        else:
            messages.error(request, "Please select a blood group and enter valid units.")

    context = {
        'stock': stock,
    }
    return render(request, 'hospital/hospital_dashboard.html', context)


@login_required
def donor_dashboard(request):
    donor = Donor.objects.get(user=request.user)
    form = LastDonationForm(instance=donor)
    donation_history = Donation.objects.filter(donor=donor).order_by('-date')
    health_record = DonorHealthCheck.objects.filter(donor=donor).order_by('-submitted_at').first()
    health_form = None

    if 'update_donation' in request.POST:
        form = LastDonationForm(request.POST, instance=donor)
        units = request.POST.get('units')
        if form.is_valid() and units:
            donor = form.save(commit=False)
            if donor.last_donation_date:
                donor.available = (date.today() - donor.last_donation_date).days >= 90
            else:
                donor.available = True
            donor.save()

            Donation.objects.create(
                donor=donor,
                date=donor.last_donation_date,
                units=units
            )
            messages.success(request, f'Donation record added — {units} unit(s) donated on {donor.last_donation_date}.')
            return redirect('donor-dashboard')
        else:
            messages.error(request, "Please enter a valid date and units.")

    elif 'submit_health' in request.POST:
        health_form = DonorHealthCheckForm(request.POST)
        if health_form.is_valid():
            health = health_form.save(commit=False)
            health.donor = donor
            health.save()
            messages.success(request, "Health form submitted! Awaiting admin approval.")
            return redirect('donor-dashboard')
        else:
            messages.error(request, f"Health form error: {health_form.errors}")
    else:
        if donor.available and (not health_record or not health_record.is_approved):
            health_form = DonorHealthCheckForm()

    context = {
        'donor': donor,
        'form': form,
        'health_form': health_form,
        'health_record': health_record,
        'donation_history': donation_history,
    }
    return render(request, 'donor/donor_dashboard.html', context)

@login_required 
def hospital_edit_profile(request): 
    hospital = get_object_or_404(Hospital, user=request.user) 
    if request.method == 'POST': 
        form = HospitalProfileForm(request.POST, instance=hospital) 
        if form.is_valid(): 
            form.save() 
            messages.success(request, "Profile updated successfully!") 
            return redirect('hospital-dashboard') 
        else: messages.error(request, "Please correct the errors below.") 
    else: form = HospitalProfileForm(instance=hospital) 
    return render(request, 'hospital/edit_profile.html', {'form': form})
@login_required 
def delete_stock(request, stock_id): 
    hospital = request.user.hospital 
    stock_item = get_object_or_404(BloodStock, id=stock_id, hospital=hospital) 
    if request.method == 'POST': 
        stock_item.delete()
        messages.success(request, f"{stock_item.blood_group} stock deleted successfully.")
        return redirect('hospital-dashboard')
    
@login_required
def submit_blood_request(request):
    patient = get_object_or_404(Patient, user=request.user)

    if request.method == 'POST':
        form = PatientRequestForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.approved = False
            patient.save()
            messages.success(request, "Blood request submitted! Awaiting admin approval.")
            return redirect('patient-dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientRequestForm(instance=patient)

    # Get patient request history
    history = Patient.objects.filter(user=request.user).order_by('-id')

    return render(request, 'patient/submit_request.html', {'form': form, 'history': history})


@login_required
def patient_dashboard(request):
    patient = Patient.objects.get(user=request.user)

    # Fetch previous blood requests (history)
    history = Patient.objects.filter(user=request.user).order_by('-id')
    no_request_message = None
    if not history.exists():
        no_request_message = "You have not submitted any blood request yet."

    context = {
        'patient': patient,
        'is_approved': patient.approved,
        'history': history,
        'no_request_message': no_request_message,
    }
    return render(request, 'patient/patient_dashboard.html', context)


@login_required
def search_hospitals(request):
    hospitals_with_stock = BloodStock.objects.filter(units__gt=0, hospital__isnull=False).select_related('hospital').order_by('hospital__name', 'blood_group')

    return render(request, 'patient/search_hospitals.html', {
        'hospitals_with_stock': hospitals_with_stock
    })


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

    hospitals_with_stock = BloodStock.objects.filter(
        blood_group__in=compatible_groups,
        units__gt=0
    ).select_related('hospital')

    return render(request, 'patient/search_donors.html', {
        'patient': patient,
        'required_blood_group': required_blood_group,
        'exact_match_donors': exact_match_donors,
        'compatible_donors': compatible_donors,
        'compatible_groups': compatible_groups,
        'hospitals_with_stock': hospitals_with_stock
    })


def is_admin(user):
    return user.is_superuser


@user_passes_test(is_admin)
def admin_dashboard(request):
    donors = Donor.objects.all()
    patients = Patient.objects.all().order_by('-approved', 'user__username')
    requested_patients = Patient.objects.filter(approved=False)
    stock = BloodStock.objects.values('blood_group').annotate(total_units=Sum('units')).order_by('blood_group')
    health_forms = DonorHealthCheck.objects.all().order_by('-submitted_at')

    total_donors = donors.count()
    available_donors = donors.filter(available=True).count()
    total_patients = patients.count()
    total_stock_units = sum(item['total_units'] for item in stock)

    if request.method == 'POST':
        if 'approve_patient' in request.POST:
            patient_id = request.POST.get('patient_id')
            patient = get_object_or_404(Patient, id=patient_id)
            patient.approved = True
            patient.save()
            messages.success(request, f"Patient {patient.user.username} approved successfully.")
            return redirect('admin-dashboard')

        if 'update_stock' in request.POST:
            stock_form = BloodStockForm(request.POST)
            if stock_form.is_valid():
                blood_group = stock_form.cleaned_data['blood_group']
                units = stock_form.cleaned_data['units']
                stock_item, created = BloodStock.objects.get_or_create(
                    blood_group=blood_group, hospital=None, defaults={'units': units}
                )
                if not created:
                    stock_item.units += units
                    stock_item.save()
                messages.success(request, f'Blood stock for {blood_group} updated successfully.')
                return redirect('admin-dashboard')

        if 'approve_health' in request.POST:
            health_id = request.POST.get('health_id')
            record = get_object_or_404(DonorHealthCheck, id=health_id)
            record.is_approved = True
            record.save()
            messages.success(request, f"{record.donor.user.username}'s health form approved!")
            return redirect('admin-dashboard')
    else:
        stock_form = BloodStockForm()

    context = {
        'donors': donors,
        'requested_patients': requested_patients,
        'patients': patients,
        'stock': stock,
        'total_donors': total_donors,
        'available_donors': available_donors,
        'total_patients': total_patients,
        'total_stock_units': total_stock_units,
        'stock_form': stock_form,
        'health_forms': health_forms,
    }

    return render(request, 'admin/admin_dashboard.html', context)
