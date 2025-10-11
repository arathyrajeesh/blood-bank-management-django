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
    
    path('patient/submit-request/', views.submit_blood_request, name='submit-blood-request'),
    path('hospital/register/', views.hospital_register, name='hospital-register'),
    path('patient/search-donors/', views.search_donors, name='search-donors'),
    path('hospital-login/', views.hospital_login, name='hospital-login'),
    path('patient/search-hospitals/', views.search_hospitals, name='search-hospitals'),
    path('hospital-dashboard/', views.hospital_dashboard, name='hospital-dashboard'),
    path('edit-profile/',views.hospital_edit_profile,name='hospital_edit_profile'),
    path('delete-stock/<int:stock_id>/', views.delete_stock, name='delete_stock'),
    path('logout/', views.logout_view, name='logout'),
]