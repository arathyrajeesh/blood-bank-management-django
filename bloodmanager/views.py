from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date, timedelta
from .models import Donor, Patient, BloodStock, Hospital, BLOOD_GROUP_CHOICES
from .forms import RegistrationForm, BloodStockForm, LastDonationForm, HospitalRegistrationForm, HospitalProfileForm


# ---------------- Home ----------------
def home(request):
    stock = BloodStock.objects.all()
    return render(request, 'index.html', {'stock': stock})


# ---------------- Registration ----------------
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


# ---------------- Login Views ----------------
def donor_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and Donor.objects.filter(user=user).exists():
            login(request, user)
            return redirect('donor-dashboard')
        messages.error(request, 'Invalid credentials or not registered as a donor.')
    return render(request, 'donor_login.html')


def patient_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and Patient.objects.filter(user=user).exists():
            login(request, user)
            return redirect('patient-dashboard')
        messages.error(request, 'Invalid credentials or not registered as a patient.')
    return render(request, 'patient_login.html')


def hospital_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and Hospital.objects.filter(user=user).exists():
            login(request, user)
            return redirect('hospital-dashboard')
        messages.error(request, 'Invalid credentials or not registered as a hospital.')
    return render(request, 'hospital/hospital_login.html')


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user and user.is_superuser:
            login(request, user)
            return redirect('admin-dashboard')
        messages.error(request, "Invalid admin credentials.")
    return render(request, 'admin_login.html')


# ---------------- Hospital Registration ----------------
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


# ---------------- Logout ----------------
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('main')


# ---------------- Hospital Dashboard ----------------
def hospital_dashboard(request):
    stock = BloodStock.objects.all()

    if request.method == 'POST':
        blood_group = request.POST['blood_group']
        units = int(request.POST['units'])
        hospital = request.user.hospital  # assuming logged in user is Hospital

        obj, created = BloodStock.objects.get_or_create(
            hospital=hospital,
            blood_group=blood_group,
            defaults={'units': units}
        )
        if not created:
            obj.units += units
            obj.save()
        return redirect('hospital-dashboard')

    context = {
        'stock': stock,
        'BLOOD_GROUP_CHOICES': BLOOD_GROUP_CHOICES,  # pass it to template
    }
    return render(request, 'hospital/hospital_dashboard.html', context)
# ---------------- Hospital Profile Edit ----------------
@login_required
def hospital_edit_profile(request):
    hospital = get_object_or_404(Hospital, user=request.user)
    if request.method == 'POST':
        form = HospitalProfileForm(request.POST, instance=hospital)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('hospital-dashboard')
    else:
        form = HospitalProfileForm(instance=hospital)

    return render(request, 'hospital/edit_profile.html', {'form': form})
@login_required
def delete_stock(request, stock_id):
    hospital = request.user.hospital
    stock_item = get_object_or_404(BloodStock, id=stock_id, hospital=hospital)
    if request.method == 'POST':
        stock_item.delete()
    return redirect('hospital-dashboard')
# ---------------- Donor Dashboard ----------------
@login_required
def donor_dashboard(request):
    donor = Donor.objects.get(user=request.user)
    if request.method == 'POST':
        form = LastDonationForm(request.POST, instance=donor)
        if form.is_valid():
            new_date = form.cleaned_data['last_donation_date']

            if new_date and (new_date == date.today() or new_date > (date.today() - timedelta(days=7))):
                try:
                    stock_item, created = BloodStock.objects.get_or_create(
                        blood_group=donor.blood_group,
                        hospital=None
                    )
                    stock_item.units += 1
                    stock_item.save()
                except Exception as e:
                    messages.warning(request, f'Stock update failed: {e}')

            form.save()
            messages.success(request, 'Last donation date updated successfully!')
            return redirect('donor-dashboard')
    else:
        form = LastDonationForm(instance=donor)

    return render(request, 'donor/donor_dashboard.html', {'donor': donor, 'form': form})


# ---------------- Patient Dashboard ----------------
@login_required
def patient_dashboard(request):
    patient = Patient.objects.get(user=request.user)
    return render(request, 'patient/patient_dashboard.html', {'patient': patient})


# ---------------- Search Donors ----------------
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

    return render(request, 'patient/search_donors.html', {
        'patient': patient,
        'required_blood_group': required_blood_group,
        'exact_match_donors': exact_match_donors,
        'compatible_donors': compatible_donors,
        'compatible_groups': compatible_groups
    })


# ---------------- Admin Dashboard ----------------
def is_admin(user):
    return user.is_superuser


@user_passes_test(is_admin)
def admin_dashboard(request):
    donors = Donor.objects.all()
    patients = Patient.objects.all()

    # Aggregate stock from all hospitals + admin stock (hospital=None)
    from django.db.models import Sum
    stock = BloodStock.objects.values('blood_group').annotate(
        total_units=Sum('units')
    ).order_by('blood_group')
    
    total_donors = donors.count()
    available_donors = donors.filter(available=True).count()
    total_patients = patients.count()
    total_stock_units = sum(item['total_units'] for item in stock)

    if request.method == 'POST':
        stock_form = BloodStockForm(request.POST)
        if stock_form.is_valid():
            blood_group = stock_form.cleaned_data['blood_group']
            units = stock_form.cleaned_data['units']

            # Admin stock entry (hospital=None)
            stock_item, created = BloodStock.objects.get_or_create(
                blood_group=blood_group,
                hospital=None,
                defaults={'units': units}
            )
            if not created:
                stock_item.units = units
                stock_item.save()

            messages.success(request, f'Blood Stock for {blood_group} updated to {units} units.')
            return redirect('admin-dashboard')
    else:
        stock_form = BloodStockForm()

    return render(request, 'admin/admin_dashboard.html', {
        'donors': donors,
        'patients': patients,
        'stock': stock,
        'total_donors': total_donors,
        'available_donors': available_donors,
        'total_patients': total_patients,
        'total_stock_units': total_stock_units,
        'stock_form': stock_form,
    })
