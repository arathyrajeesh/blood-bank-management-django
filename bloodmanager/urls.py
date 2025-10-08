from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name='main'),
    path('donor-login/',views.donor_login,name='donor-login'),
    path('admin-login/',views.admin_login,name='admin-login'),
    path('patient-login/',views.patient_login,name='patient-login'),
    path('register/',views.register,name='register'),
    
    path('donor-dashboard/', views.donor_dashboard, name='donor-dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('patient-dashboard/', views.patient_dashboard, name='patient-dashboard'),
    
    path('hospital/register/', views.hospital_register, name='hospital-register'),
    path('patient/search-donors/', views.search_donors, name='search-donors'),
    path('hospital-login/', views.hospital_login, name='hospital-login'),
    path('hospital-dashboard/', views.hospital_dashboard, name='hospital-dashboard'),
    path('logout/', views.logout_view, name='logout'),
]