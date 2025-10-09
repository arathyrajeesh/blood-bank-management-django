from django.contrib import admin
from .models import Donor, Patient,BloodStock,Hospital,DonorHealthCheck

admin.site.register(Donor)
admin.site.register(Patient)
admin.site.register(BloodStock)
admin.site.register(Hospital)
admin.site.register(DonorHealthCheck)


