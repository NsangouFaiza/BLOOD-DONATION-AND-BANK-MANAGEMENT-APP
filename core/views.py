from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import json
import random
import string
from datetime import datetime, timedelta
from .models import *
from .forms import *

def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.user_type == 'admin'

def is_staff(user):
    """Check if user is blood bank staff"""
    return user.is_authenticated and user.user_type == 'staff'

def is_lab_tech(user):
    """Check if user is lab technician"""
    return user.is_authenticated and user.user_type == 'lab_tech'

def is_donor(user):
    """Check if user is donor"""
    return user.is_authenticated and user.user_type == 'donor'

def is_patient(user):
    """Check if user is patient"""
    return user.is_authenticated and user.user_type == 'patient'

def home(request):
    """Home page"""
    context = {
        'total_donors': Donor.objects.filter(is_eligible=True).count(),
        'total_patients': Patient.objects.count(),
        'total_hospitals': Hospital.objects.filter(is_active=True).count(),
        'available_blood': BloodUnit.objects.filter(status='ready').count(),
    }
    return render(request, 'core/home.html', context)

def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified = False
            user.save()
            
            # Generate OTP (in real app, send via SMS)
            otp_code = ''.join(random.choices(string.digits, k=6))
            expires_at = timezone.now() + timedelta(minutes=10)
            
            OTPVerification.objects.create(
                user=user,
                otp_code=otp_code,
                expires_at=expires_at
            )
            
            # In real app, send OTP via SMS
            messages.success(request, f'Account created! OTP sent to your phone. OTP: {otp_code}')
            return redirect('verify_otp', user_id=user.id)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})

def verify_otp(request, user_id):
    """OTP verification"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            try:
                otp_verification = OTPVerification.objects.get(
                    user=user,
                    otp_code=otp_code,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                
                otp_verification.is_used = True
                otp_verification.save()
                
                user.is_verified = True
                user.save()
                
                messages.success(request, 'Account verified successfully! Please complete your profile.')
                
                if user.user_type == 'donor':
                    return redirect('complete_donor_profile')
                elif user.user_type == 'patient':
                    return redirect('complete_patient_profile')
                else:
                    return redirect('login')
                    
            except OTPVerification.DoesNotExist:
                messages.error(request, 'Invalid or expired OTP code.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'core/verify_otp.html', {'form': form, 'user': user})

def complete_donor_profile(request):
    """Complete donor profile after OTP verification"""
    if not request.user.is_authenticated or request.user.user_type != 'donor':
        return redirect('login')
    
    if request.method == 'POST':
        form = DonorProfileForm(request.POST)
        if form.is_valid():
            donor = form.save(commit=False)
            donor.user = request.user
            donor.save()
            messages.success(request, 'Donor profile completed! Please wait for lab verification.')
            return redirect('donor_dashboard')
    else:
        form = DonorProfileForm()
    
    return render(request, 'core/complete_donor_profile.html', {'form': form})

def complete_patient_profile(request):
    """Complete patient profile after OTP verification"""
    if not request.user.is_authenticated or request.user.user_type != 'patient':
        return redirect('login')
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user
            patient.save()
            messages.success(request, 'Patient profile completed!')
            return redirect('patient_dashboard')
    else:
        form = PatientProfileForm()
    
    return render(request, 'core/complete_patient_profile.html', {'form': form})

def user_login(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_verified:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            if user.user_type == 'admin':
                return redirect('admin_dashboard')
            elif user.user_type == 'staff':
                return redirect('staff_dashboard')
            elif user.user_type == 'lab_tech':
                return redirect('lab_tech_dashboard')
            elif user.user_type == 'donor':
                return redirect('donor_dashboard')
            elif user.user_type == 'patient':
                return redirect('patient_dashboard')
        else:
            messages.error(request, 'Invalid credentials or account not verified.')
    
    return render(request, 'core/login.html')

def user_logout(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def donor_dashboard(request):
    """Donor dashboard"""
    if not is_donor(request.user):
        return redirect('home')
    
    try:
        donor = Donor.objects.get(user=request.user)
        appointments = Appointment.objects.filter(donor=donor).order_by('-appointment_date')
        matches = DonorPatientMatch.objects.filter(donor=donor).order_by('-created_at')
        
        context = {
            'donor': donor,
            'appointments': appointments[:5],
            'matches': matches[:5],
            'total_donations': BloodUnit.objects.filter(donor=donor).count(),
        }
    except Donor.DoesNotExist:
        return redirect('complete_donor_profile')
    
    return render(request, 'core/donor_dashboard.html', context)

@login_required
def patient_dashboard(request):
    """Patient dashboard"""
    if not is_patient(request.user):
        return redirect('home')
    
    try:
        patient = Patient.objects.get(user=request.user)
        blood_requests = BloodRequest.objects.filter(patient=patient).order_by('-created_at')
        matches = DonorPatientMatch.objects.filter(patient=patient).order_by('-created_at')
        
        context = {
            'patient': patient,
            'blood_requests': blood_requests[:5],
            'matches': matches[:5],
        }
    except Patient.DoesNotExist:
        return redirect('complete_patient_profile')
    
    return render(request, 'core/patient_dashboard.html', context)

@login_required
def staff_dashboard(request):
    """Blood bank staff dashboard"""
    if not is_staff(request.user):
        return redirect('home')
    
    # NOTE: The original queryset attempted to filter by a relationship chain
    # `blood_bank__hospital__bloodbank__user` which does not exist in models.
    # Until a proper ownership relation is modeled, show recent global data.
    appointments = Appointment.objects.all().order_by('-appointment_date')
    blood_units = BloodUnit.objects.all().order_by('-created_at')
    
    context = {
        'appointments': appointments[:10],
        'blood_units': blood_units[:10],
        'total_appointments': appointments.count(),
        'total_blood_units': blood_units.count(),
    }
    
    return render(request, 'core/staff_dashboard.html', context)

@login_required
def lab_tech_dashboard(request):
    """Lab technician dashboard"""
    if not is_lab_tech(request.user):
        return redirect('home')
    
    pending_tests = BloodTest.objects.filter(status='pending').order_by('-created_at')
    completed_tests = BloodTest.objects.filter(status='completed').order_by('-created_at')
    
    context = {
        'pending_tests': pending_tests[:10],
        'completed_tests': completed_tests[:10],
        'total_pending': pending_tests.count(),
        'total_completed': completed_tests.count(),
    }
    
    return render(request, 'core/lab_tech_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    if not is_admin(request.user):
        return redirect('home')
    
    context = {
        'total_users': User.objects.count(),
        'total_donors': Donor.objects.count(),
        'total_patients': Patient.objects.count(),
        'total_hospitals': Hospital.objects.count(),
        'total_blood_units': BloodUnit.objects.count(),
        'recent_users': User.objects.order_by('-created_at')[:5],
    }
    
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def book_appointment(request):
    """Book donor appointment"""
    if not is_donor(request.user):
        return redirect('home')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.donor = Donor.objects.get(user=request.user)
            appointment.save()
            messages.success(request, 'Appointment booked successfully!')
            return redirect('donor_dashboard')
    else:
        form = AppointmentForm()
    
    return render(request, 'core/book_appointment.html', {'form': form})

@login_required
def request_blood(request):
    """Patient blood request"""
    if not is_patient(request.user):
        return redirect('home')
    
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.patient = Patient.objects.get(user=request.user)
            blood_request.save()
            
            # Find matching donors
            matching_donors = Donor.objects.filter(
                blood_type=blood_request.blood_type_needed,
                is_eligible=True
            )
            
            # Create donor-patient matches
            for donor in matching_donors:
                DonorPatientMatch.objects.create(
                    donor=donor,
                    patient=blood_request.patient,
                    blood_request=blood_request
                )
            
            messages.success(request, f'Blood request submitted! Found {matching_donors.count()} matching donors.')
            return redirect('patient_dashboard')
    else:
        form = BloodRequestForm()
    
    return render(request, 'core/request_blood.html', {'form': form})

@login_required
def view_donors(request):
    """View available donors for patients"""
    if not is_patient(request.user):
        return redirect('home')
    
    try:
        patient = Patient.objects.get(user=request.user)
        blood_type = patient.blood_type_needed
        
        donors = Donor.objects.filter(
            blood_type=blood_type,
            is_eligible=True
        ).select_related('user')
        
        paginator = Paginator(donors, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'donors': page_obj,
            'blood_type': blood_type,
        }
        
    except Patient.DoesNotExist:
        return redirect('complete_patient_profile')
    
    return render(request, 'core/view_donors.html', context)

@login_required
def view_blood_inventory(request):
    """View blood inventory for staff"""
    if not is_staff(request.user):
        return redirect('home')
    
    blood_units = BloodUnit.objects.all().order_by('-created_at')
    
    # Filter by blood type
    blood_type = request.GET.get('blood_type')
    if blood_type:
        blood_units = blood_units.filter(blood_type=blood_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        blood_units = blood_units.filter(status=status)
    
    paginator = Paginator(blood_units, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'blood_units': page_obj,
        'blood_types': BloodUnit.BLOOD_TYPES,
        'statuses': BloodUnit.STATUS_CHOICES,
    }
    
    return render(request, 'core/view_blood_inventory.html', context)

@login_required
def record_blood_test(request):
    """Record blood test results for lab technicians"""
    if not is_lab_tech(request.user):
        return redirect('home')
    
    if request.method == 'POST':
        form = BloodTestForm(request.POST)
        if form.is_valid():
            blood_test = form.save(commit=False)
            blood_test.lab_technician = request.user
            blood_test.save()
            
            # Update donor eligibility if test is completed
            if blood_test.status == 'completed' and blood_test.donor:
                donor = blood_test.donor
                donor.is_eligible = True
                donor.blood_type = blood_test.results.split()[0] if blood_test.results else None
                donor.save()
            
            messages.success(request, 'Blood test results recorded successfully!')
            return redirect('lab_tech_dashboard')
    else:
        form = BloodTestForm()
    
    return render(request, 'core/record_blood_test.html', {'form': form})

@login_required
def manage_appointments(request):
    """Manage appointments for staff"""
    if not is_staff(request.user):
        return redirect('home')
    
    appointments = Appointment.objects.all().order_by('-appointment_date')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        appointments = appointments.filter(status=status)
    
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        new_status = request.POST.get('new_status')
        
        if appointment_id and new_status:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            appointment.status = new_status
            appointment.save()
            messages.success(request, 'Appointment status updated!')
            return redirect('manage_appointments')
    
    paginator = Paginator(appointments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'appointments': page_obj,
        'statuses': Appointment.STATUS_CHOICES,
    }
    
    return render(request, 'core/manage_appointments.html', context)

@login_required
def donor_patient_matches(request):
    """View and manage donor-patient matches"""
    if not (is_donor(request.user) or is_patient(request.user)):
        return redirect('home')
    
    if is_donor(request.user):
        matches = DonorPatientMatch.objects.filter(donor__user=request.user)
    else:
        matches = DonorPatientMatch.objects.filter(patient__user=request.user)
    
    matches = matches.order_by('-created_at')
    
    if request.method == 'POST':
        match_id = request.POST.get('match_id')
        response = request.POST.get('response')
        response_type = request.POST.get('response_type')
        
        if match_id and response and response_type:
            match = get_object_or_404(DonorPatientMatch, id=match_id)
            
            if response_type == 'donor_response' and is_donor(request.user):
                match.donor_response = response
                match.status = 'accepted' if 'accept' in response.lower() else 'declined'
            elif response_type == 'patient_response' and is_patient(request.user):
                match.patient_response = response
                match.status = 'accepted' if 'accept' in response.lower() else 'declined'
            
            match.save()
            messages.success(request, 'Response recorded successfully!')
            return redirect('donor_patient_matches')
    
    paginator = Paginator(matches, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'matches': page_obj,
        'user_type': request.user.user_type,
    }
    
    return render(request, 'core/donor_patient_matches.html', context)

@login_required
def search_donors(request):
    """Search for donors by blood type and location"""
    query = request.GET.get('q', '')
    blood_type = request.GET.get('blood_type', '')
    city = request.GET.get('city', '')
    
    donors = Donor.objects.filter(is_eligible=True)
    
    if query:
        donors = donors.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
    
    if blood_type:
        donors = donors.filter(blood_type=blood_type)
    
    if city:
        donors = donors.filter(user__city__icontains=city)
    
    donors = donors.select_related('user').order_by('-created_at')
    
    paginator = Paginator(donors, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'donors': page_obj,
        'query': query,
        'blood_type': blood_type,
        'city': city,
        'blood_types': Donor.BLOOD_TYPES,
    }
    
    return render(request, 'core/search_donors.html', context)

@login_required
def user_profile(request):
    """User profile view and edit"""
    if request.method == 'POST':
        # Handle profile updates
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')
    
    return render(request, 'core/user_profile.html')

@login_required
def notifications(request):
    """User notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark as read
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(id=notification_id, user=request.user)
                notification.is_read = True
                notification.save()
            except Notification.DoesNotExist:
                pass
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
    }
    
    return render(request, 'core/notifications.html', context)

# -------------------------
# Community & Maps Views
# -------------------------
def campaigns(request):
    """Public page to list active donation campaigns and updates."""
    active_campaigns = Campaign.objects.filter(is_active=True).order_by('-start_date')
    return render(request, 'core/campaigns.html', { 'campaigns': active_campaigns })


def hospitals_map(request):
    """Interactive map page to locate hospitals/blood banks and show stock levels."""
    return render(request, 'core/hospitals_map.html')


# -------------------------
# JSON API Endpoints
# -------------------------
def api_hospitals(request):
    """Return hospitals with geolocation for map display."""
    hospitals = Hospital.objects.filter(is_active=True)
    data = []
    for h in hospitals:
        data.append({
            'id': h.id,
            'name': h.name,
            'city': h.city,
            'phone': h.phone,
            'email': h.email,
            'latitude': float(h.latitude) if h.latitude is not None else None,
            'longitude': float(h.longitude) if h.longitude is not None else None,
        })
    return JsonResponse({ 'hospitals': data })


def api_inventory(request):
    """Return real-time stock levels per hospital grouped by blood type and status."""
    # Aggregate BloodUnit by hospital, blood_type, status
    units = BloodUnit.objects.select_related('blood_bank__hospital')
    stock = {}
    for u in units:
        hospital = u.blood_bank.hospital
        hid = hospital.id
        if hid not in stock:
            stock[hid] = {
                'hospital': hospital.name,
                'city': hospital.city,
                'latitude': float(hospital.latitude) if hospital.latitude is not None else None,
                'longitude': float(hospital.longitude) if hospital.longitude is not None else None,
                'by_blood_type': {},
            }
        bt = u.blood_type
        status = u.status
        stock[hid]['by_blood_type'].setdefault(bt, { 'ready': 0, 'testing': 0, 'reserved': 0, 'used': 0, 'expired': 0, 'collected': 0, 'rejected': 0 })
        if status in stock[hid]['by_blood_type'][bt]:
            stock[hid]['by_blood_type'][bt][status] += 1
        else:
            stock[hid]['by_blood_type'][bt][status] = 1
    # Transform to list
    result = []
    for hid, info in stock.items():
        by_type = []
        for bt, counters in info['by_blood_type'].items():
            total_ready = counters.get('ready', 0)
            by_type.append({ 'blood_type': bt, 'counts': counters, 'ready': total_ready })
        result.append({
            'hospital_id': hid,
            **{k: v for k, v in info.items() if k != 'by_blood_type'},
            'by_blood_type': by_type,
        })
    return JsonResponse({ 'inventory': result })
