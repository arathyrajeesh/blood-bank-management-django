from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request,'index.html')
def admin_login(request):
    return render(request,'admin_login.html')
def patient_login(request):
    return render(request,'patient_login.html')
def donor_login(request):
    return render(request,'donor_login.html')
def register(request):
    return render(request,'register.html')


