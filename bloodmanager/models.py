from django.db import models
from django.contrib.auth.models import User
from datetime import date

BLOOD_GROUP_CHOICES = [
    ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
]

GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]


class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    address = models.TextField()
    age = models.PositiveIntegerField()
    last_donation_date = models.DateField(null=True, blank=True)
    available = models.BooleanField(default=True)
    profile_photo = models.ImageField(
        upload_to='donor_photos/', 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} ({self.blood_group})"

    def save(self, *args, **kwargs):
        if self.last_donation_date and (date.today() - self.last_donation_date).days < 90:
            self.available = False
        else:
            self.available = True
        super().save(*args, **kwargs)

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=10)
    blood_group = models.CharField(max_length=5)
    address = models.TextField()
    required_units = models.PositiveIntegerField(default=1)
    approved = models.BooleanField(default=False)
    hospital = models.ForeignKey('Hospital', on_delete=models.SET_NULL, null=True, blank=True, related_name='requests')  # ✅ NEW



class Hospital(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(null=True, blank=True)  # <-- add this

    def __str__(self):
        return self.name

class BloodStock(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, null=True, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    units = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.hospital.name} - {self.blood_group}: {self.units}"


class DonorHealthCheck(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    weight = models.FloatField()
    hemoglobin_level = models.FloatField()
    has_disease = models.BooleanField(default=False)
    recent_medications = models.TextField(blank=True, null=True)
    recent_surgeries = models.TextField(blank=True, null=True)
    tattoos_or_piercings = models.TextField(blank=True, null=True)
    travel_history = models.TextField(blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    
    is_approved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor.user.username} - Health Check"

class Donation(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    date = models.DateField()
    units = models.PositiveIntegerField(default=1)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor.user.username} donated {self.units} unit(s) on {self.date}"

class DonationSlot(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    approved = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.donor.user.username} - {self.date} {self.time}"

    def mark_completed(self, units=1):
        self.completed = True
        self.save()

        stock, created = BloodStock.objects.get_or_create(
            blood_group=self.donor.blood_group,
            hospital=None,
            defaults={'units': units}
        )
        if not created:
            stock.units += units
            stock.save()


class BloodRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=5)
    units = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.user.username} → {self.hospital.name} ({self.blood_group})"
