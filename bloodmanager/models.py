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
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    address = models.TextField()
    required_units = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.blood_group}"


class BloodStock(models.Model):
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, unique=True)
    units = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Stock: {self.blood_group} - {self.units} units"
    
    
    
class Hospital(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.user.username})"
