from django.contrib import admin
from .models import Donor, Patient,BloodStock,Hospital,DonorHealthCheck,Donation,DonationSlot

admin.site.register(Donor)
admin.site.register(Patient)
admin.site.register(BloodStock)
admin.site.register(Hospital)
admin.site.register(DonorHealthCheck)
admin.site.register(Donation)

@admin.register(DonationSlot)
class DonationSlotAdmin(admin.ModelAdmin):
    list_display = ('donor', 'hospital', 'date', 'time', 'approved')
    list_filter = ('approved', 'hospital', 'date')
    search_fields = ('donor__user__username', 'hospital__name')
