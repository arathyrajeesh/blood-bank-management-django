from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date,timedelta
from django.db.models import Sum
from .models import ( Donor, Patient, BloodStock, Hospital,DonorHealthCheck, Donation,DonationSlot)
from .forms import (RegistrationForm, BloodStockForm, LastDonationForm,HospitalRegistrationForm, HospitalProfileForm,DonorHealthCheckForm, PatientRequestForm,DonorProfileForm)
from .forms import BloodStockForm
import matplotlib.pyplot as plt
import io, base64
from .models import BloodRequest

def home(request):
    stock = BloodStock.objects.values('blood_group').annotate(units=Sum('units')).order_by('blood_group')
    return render(request, 'index.html', {'stock': stock})

def help(request):
    return render(request,'Help.html')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)  
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
                profile_photo = form.cleaned_data.get('profile_photo') 
                Donor.objects.create(
                    user=user,
                    phone=phone,
                    gender=gender,
                    blood_group=blood_group,
                    address=address,
                    age=age,
                    profile_photo=profile_photo
                )
            elif role == 'patient':
                required_units = form.cleaned_data.get('required_units') or 1
                Patient.objects.create(
                    user=user,
                    phone=phone,
                    gender=gender,
                    blood_group=blood_group,
                    address=address,
                    required_units=required_units
                )
            elif role == 'hospital':
                name = form.cleaned_data['name']
                Hospital.objects.create(
                    user=user,
                    name=name,
                    phone=phone,
                    address=address
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
            if role == 'donor' and Donor.objects.filter(user=user).exists():
                login(request, user)
                return redirect('donor-dashboard')

            elif role == 'patient' and Patient.objects.filter(user=user).exists():
                login(request, user)
                return redirect('patient-dashboard')

            elif role == 'hospital' and Hospital.objects.filter(user=user).exists():
                login(request, user)
                return redirect('hospital-dashboard')

            elif role == 'admin' and user.is_superuser:
                login(request, user)
                return redirect('admin-dashboard')

            else:
                messages.error(request, f"You are not registered as a {role}.")
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html')

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
            return redirect('login')
    else:
        form = HospitalRegistrationForm()

    return render(request, 'hospital/hospital_register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('main')


@login_required
def hospital_dashboard(request):
    hospital = request.user.hospital  # current logged-in hospital
    stock = BloodStock.objects.filter(hospital=hospital)

    pending_requests = BloodRequest.objects.filter(hospital=hospital, status='Pending').select_related('patient', 'patient__user').order_by('-created_at')

    approved_requests = BloodRequest.objects.filter(hospital=hospital, status='Approved').select_related('patient', 'patient__user').order_by('-created_at')[:5]

    recent_slots = DonationSlot.objects.filter(hospital=hospital).select_related('donor', 'donor__user').order_by('-date', '-time')[:5]

    if request.method == 'POST':
        if 'add_stock' in request.POST:
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

        elif 'approve_request' in request.POST:
            req_id = request.POST.get('request_id')
            req = get_object_or_404(BloodRequest, id=req_id, hospital=hospital)

            stock_item = BloodStock.objects.filter(hospital=hospital, blood_group=req.blood_group).first()

            if stock_item and stock_item.units >= req.units:
                stock_item.units -= req.units
                stock_item.save()

                req.status = 'Approved'
                req.save()

                messages.success(
                    request,
                    f"Approved {req.units} unit(s) of {req.blood_group} for {req.patient.user.username}."
                )
            else:
                messages.error(
                    request,
                    f"Not enough stock to approve request for {req.patient.user.username}!"
                )

            return redirect('hospital-dashboard')

        elif 'reject_request' in request.POST:
            req_id = request.POST.get('request_id')
            req = get_object_or_404(BloodRequest, id=req_id, hospital=hospital)
            req.status = 'Rejected'
            req.save()
            messages.warning(request, f"Rejected request from {req.patient.user.username}.")
            return redirect('hospital-dashboard')

    context = {
        'stock': stock,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'recent_slots': recent_slots,
        'BLOOD_GROUP_CHOICES': getattr(BloodStock, 'BLOOD_GROUP_CHOICES', [
            ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
        ]),
    }

    return render(request, 'hospital/hospital_dashboard.html', context)

@login_required
def donor_dashboard(request):
    donor = Donor.objects.get(user=request.user)
    form = LastDonationForm(instance=donor)
    donation_history = Donation.objects.filter(donor=donor).order_by('-date')
    health_record = DonorHealthCheck.objects.filter(donor=donor).order_by('-submitted_at').first()
    slot = DonationSlot.objects.filter(donor=donor, approved=True).order_by('-date', '-time').first() 
    rejected_message = None
    health_form = None

    total_units = donation_history.aggregate(total=Sum('units'))['total'] or 0

    if health_record and not health_record.is_approved and getattr(health_record, 'admin_rejected', False):
        rejected_message = "Your health form was rejected. Please resubmit with correct details."
        health_form = DonorHealthCheckForm(instance=health_record)
    elif donor.available and (not health_record or not health_record.is_approved):
        health_form = DonorHealthCheckForm()

    if request.method == 'POST':
        if 'accept_slot' in request.POST:
            slot_id = request.POST.get('accept_slot')
            slot = get_object_or_404(DonationSlot, id=slot_id, donor=donor)
            slot.accepted = True
            slot.save()
            messages.success(request, "You have accepted your donation slot.")
            return redirect('donor-dashboard')

        elif 'reject_slot' in request.POST:
            slot_id = request.POST.get('reject_slot')
            slot = get_object_or_404(DonationSlot, id=slot_id, donor=donor)
            slot.delete()
            messages.warning(request, "You have rejected your donation slot.")
            return redirect('donor-dashboard')

        elif 'update_donation' in request.POST:
            form = LastDonationForm(request.POST, instance=donor)
            units = request.POST.get('units')

            if form.is_valid() and units:
                new_donation_date = form.cleaned_data['last_donation_date']

                if donor.last_donation_date:
                    days_since_last = (new_donation_date - donor.last_donation_date).days
                    if days_since_last < 90:
                        messages.error(
                            request,
                            f"You can donate only after 90 days! ({90 - days_since_last} days remaining)"
                        )
                        return redirect('donor-dashboard')

                donor.last_donation_date = new_donation_date
                donor.available = False
                donor.save()

                donation = Donation.objects.create(
                    donor=donor,
                    date=new_donation_date,
                    units=units
                )

                if slot and slot.accepted and not slot.completed:
                    slot.completed = True
                    slot.save()

                    stock, created = BloodStock.objects.get_or_create(
                        blood_group=donor.blood_group,
                        hospital=None,
                        defaults={'units': int(units)}
                    )
                    if not created:
                        stock.units += int(units)
                        stock.save()

                messages.success(
                    request,
                    f"Donation recorded: {units} unit(s) on {new_donation_date}. "
                    f"Next donation allowed after 90 days."
                )
                return redirect('donor-dashboard')
            else:
                messages.error(request, "Please enter a valid date and units.")

        # 4️⃣ Donor submits or resubmits health form
        elif 'submit_health' in request.POST:
            if health_record and getattr(health_record, 'admin_rejected', False):
                health_form = DonorHealthCheckForm(request.POST, instance=health_record)
            else:
                health_form = DonorHealthCheckForm(request.POST)
            
            if health_form.is_valid():
                health = health_form.save(commit=False)
                health.donor = donor
                health.admin_rejected = False  
                health.save()
                messages.success(request, "Health form submitted! Awaiting admin approval.")
                return redirect('donor-dashboard')
            else:
                messages.error(request, f"Health form error: {health_form.errors}")

    next_eligible_date = None
    if donor.last_donation_date:
        next_eligible_date = donor.last_donation_date + timedelta(days=90)

    context = {
        'donor': donor,
        'form': form,
        'health_form': health_form,
        'health_record': health_record,
        'donation_history': donation_history,
        'next_eligible_date': next_eligible_date,
        'today': date.today(),
        'rejected_message': rejected_message,
        'total_units': total_units,
        'slot': slot,  
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
def donor_edit_profile(request):
    donor = request.user.donor 
    if request.method == 'POST':
        form = DonorProfileForm(request.POST, request.FILES, instance=donor)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('donor-dashboard')
    else:
        form = DonorProfileForm(instance=donor)
    return render(request, 'donor/donor_edit_profile.html', {'form': form})

@login_required
def submit_blood_request(request):
    patient = get_object_or_404(Patient, user=request.user)

    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        blood_group = request.POST.get('blood_group_request')
        units = request.POST.get('units_request')

        hospital = get_object_or_404(Hospital, id=hospital_id)

        BloodRequest.objects.create(
            patient=patient,
            hospital=hospital,
            blood_group=blood_group,
            units=units,
            status='Pending'
        )

        messages.success(request, f"Your request for {units} unit(s) of {blood_group} was sent to {hospital.name}.")
        return redirect('patient-dashboard')

    hospitals_with_stock = BloodStock.objects.filter(units__gt=0).select_related('hospital')
    return render(request, 'patient/search_hospitals.html', {'hospitals_with_stock': hospitals_with_stock})


@login_required
def patient_dashboard(request):
    patient = get_object_or_404(Patient, user=request.user)

    history = BloodRequest.objects.filter(patient=patient).select_related('hospital').order_by('-created_at')

    received_requests = history.filter(status='Approved')

    no_request_message = None
    if not history.exists():
        no_request_message = "You have not submitted any blood requests yet."

    context = {
        'patient': patient,
        'is_approved': patient.approved,
        'history': history,
        'received_requests': received_requests,  
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
    patient_requests = BloodRequest.objects.select_related('patient', 'hospital').order_by('-created_at')

    total_donors = donors.count()
    available_donors = donors.filter(available=True).count()
    total_patients = patients.count()
    total_stock_units = sum(item['total_units'] for item in stock)

    stock_form = BloodStockForm()

    approved_donors = Donor.objects.filter(
    available=True,
    donorhealthcheck__is_approved=True  
    ).exclude(
        donationslot__completed=False
    ).distinct()

    hospitals = Hospital.objects.all()
    recent_slots = DonationSlot.objects.select_related('donor', 'hospital').order_by('-date', '-time')[:5]

    latest_slot_per_donor = {}
    for donor in donors:
        slot = donor.donationslot_set.order_by('-date', '-time').first()
        if slot:
            latest_slot_per_donor[donor.id] = slot

    if request.method == 'POST':

        if 'assign_slot' in request.POST:
            donor_id = request.POST.get('donor_id')
            hospital_id = request.POST.get('hospital_id')
            date = request.POST.get('date')
            time = request.POST.get('time')

            donor = get_object_or_404(Donor, id=donor_id)
            hospital = get_object_or_404(Hospital, id=hospital_id)

            DonationSlot.objects.create(
                donor=donor,
                hospital=hospital,
                date=date,
                time=time,
                approved=True,
                accepted=False,
                completed=False
            )

            messages.success(request, f"Slot assigned to {donor.user.username} successfully!")
            return redirect('admin-dashboard')


        if 'approve_patient' in request.POST:
            patient_id = request.POST.get('patient_id')
            patient = get_object_or_404(Patient, id=patient_id)
            patient.approved = True
            patient.save()
            messages.success(request, f"Patient {patient.user.username} approved successfully.")
            return redirect('admin-dashboard')

        if 'reject_health' in request.POST:
            health_id = request.POST.get('health_id')
            record = get_object_or_404(DonorHealthCheck, id=health_id)
            donor_user = record.donor.user
            record.delete()
            request.session['health_form_rejected'] = "Your health form was rejected by admin. Please submit a new one."
            messages.success(request, f"Health form for {donor_user.username} rejected.")
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

    total_units = sum(item['total_units'] for item in stock)
    stock_with_percentage = []
    for item in stock:
        percent = (item['total_units'] / total_units * 100) if total_units > 0 else 0
        stock_with_percentage.append({
            'blood_group': item['blood_group'],
            'total_units': item['total_units'],
            'percentage': round(percent, 1),
        })

    labels = [item['blood_group'] for item in stock]
    quantities = [item['total_units'] for item in stock]

    plt.switch_backend('AGG')
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(quantities, labels=labels, startangle=90)
    ax.set_title("Blood Stock Distribution")

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    chart = base64.b64encode(image_png).decode('utf-8')
    plt.close(fig)

    context = {
        'donors': donors,
        'requested_patients': requested_patients,
        'patients': patients,
        'stock': stock_with_percentage,
        'total_donors': total_donors,
        'available_donors': available_donors,
        'total_patients': total_patients,
        'total_stock_units': total_stock_units,
        'stock_form': stock_form,
        'health_forms': health_forms,
        'chart': chart,
        'approved_donors': approved_donors,
        'hospitals': Hospital.objects.all(),
        'recent_slots': recent_slots,              
        'latest_slot_per_donor': latest_slot_per_donor,
        'patient_requests': patient_requests,

    }

    return render(request, 'admin/admin_dashboard.html', context)