from django.urls import path

from . import views

urlpatterns = [
    path('',views.home,name='main'),
    path('donor-login/',views.donor_login,name='donor-login'),
    path('admin-login/',views.admin_login,name='admin-login'),
    path('patient-login/',views.patient_login,name='patient-login'),
    path('register/',views.register,name='register'),
]