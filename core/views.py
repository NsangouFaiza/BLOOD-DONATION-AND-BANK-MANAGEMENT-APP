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

# Staff user type removed - functionality moved to admin

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
            messages.success(request, f'✅ Account created successfully! Your OTP code is: <strong>{otp_code}</strong><br>📱 Please enter this code on the next page to verify your account. <br>⏰ This code will expire in 10 minutes.')
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
            # Staff user type removed
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
    """Enhanced donor dashboard with comprehensive data"""
    if not is_donor(request.user):
        return redirect('home')
    
    try:
        donor = Donor.objects.get(user=request.user)
        
        # Get appointments data
        appointments = Appointment.objects.filter(donor=donor).order_by('-appointment_date')
        upcoming_appointments = appointments.filter(
            appointment_date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        )
        
        # Get donor-patient matches
        matches = DonorPatientMatch.objects.filter(donor=donor).order_by('-created_at')
        pending_matches = matches.filter(status='pending')
        
        # Get donation history
        blood_units = BloodUnit.objects.filter(donor=donor).order_by('-collection_date')
        total_donations = blood_units.count()
        
        # Calculate eligibility status
        can_donate = True
        eligibility_message = "You are eligible to donate"
        
        if donor.last_donation_date:
            days_since_last = (timezone.now().date() - donor.last_donation_date).days
            if days_since_last < 56:  # 8 weeks minimum between donations
                can_donate = False
                eligibility_message = f"You can donate again in {56 - days_since_last} days"
        
        # Get recent notifications
        notifications = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).order_by('-created_at')[:5]
        
        context = {
            'donor': donor,
            'appointments': upcoming_appointments[:5],
            'all_appointments': appointments[:10],
            'matches': matches[:5],
            'pending_matches': pending_matches,
            'total_donations': total_donations,
            'recent_donations': blood_units[:5],
            'can_donate': can_donate,
            'eligibility_message': eligibility_message,
            'notifications': notifications,
            'upcoming_appointments_count': upcoming_appointments.count(),
            'pending_matches_count': pending_matches.count(),
        }
    except Donor.DoesNotExist:
        return redirect('complete_donor_profile')
    
    return render(request, 'core/donor_dashboard.html', context)

@login_required
def patient_dashboard(request):
    """Enhanced patient dashboard with comprehensive data"""
    if not is_patient(request.user):
        return redirect('home')
    
    try:
        patient = Patient.objects.get(user=request.user)
        
        # Get blood requests data
        blood_requests = BloodRequest.objects.filter(patient=patient).order_by('-created_at')
        pending_requests = blood_requests.filter(status='pending')
        approved_requests = blood_requests.filter(status='approved')
        fulfilled_requests = blood_requests.filter(status='fulfilled')
        
        # Get donor matches
        matches = DonorPatientMatch.objects.filter(patient=patient).order_by('-created_at')
        active_matches = matches.filter(status__in=['pending', 'accepted'])
        successful_matches = matches.filter(status='completed')
        
        # Find compatible donors
        compatible_donors = Donor.objects.filter(
            blood_type=patient.blood_type_needed,
            is_eligible=True
        ).select_related('user')
        
        # Get available blood units
        available_blood_units = BloodUnit.objects.filter(
            blood_type=patient.blood_type_needed,
            status='ready'
        ).count()
        
        # Get recent notifications
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:5]
        
        # Calculate urgency status
        urgent_requests = blood_requests.filter(
            urgency_level__in=['high', 'emergency'],
            status__in=['pending', 'approved']
        )
        
        context = {
            'patient': patient,
            'blood_requests': blood_requests[:5],
            'matches': matches[:5],
            'blood_requests_count': blood_requests.count(),
            'active_matches_count': active_matches.count(),
            'pending_requests_count': pending_requests.count(),
            'total_matches_count': matches.count(),
            'compatible_donors': compatible_donors[:10],
            'compatible_donors_count': compatible_donors.count(),
            'available_blood_units': available_blood_units,
            'notifications': notifications,
            'urgent_requests': urgent_requests,
            'urgent_requests_count': urgent_requests.count(),
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'fulfilled_requests': fulfilled_requests,
        }
    except Patient.DoesNotExist:
        return redirect('complete_patient_profile')
    
    return render(request, 'core/patient_dashboard.html', context)

# Staff dashboard removed - functionality moved to admin dashboard

@login_required
def lab_tech_dashboard(request):
    """Enhanced lab technician dashboard"""
    if not is_lab_tech(request.user):
        return redirect('home')
    
    # Get today's date for filtering
    today = timezone.now().date()
    
    # Get blood tests data
    all_tests = BloodTest.objects.all().order_by('-created_at')
    pending_tests = all_tests.filter(status='pending')
    completed_tests = all_tests.filter(status='completed')
    failed_tests = all_tests.filter(status='failed')
    in_progress_tests = all_tests.filter(status='in_progress')
    
    # Today's tests
    today_tests = all_tests.filter(test_date__date=today)
    today_completed = today_tests.filter(status='completed')
    
    # Get donors needing testing
    donors_needing_tests = Donor.objects.filter(
        is_eligible=False,
        bloodtest__isnull=True
    ).distinct()
    
    # Get recent blood units for testing
    recent_blood_units = BloodUnit.objects.filter(
        status='testing'
    ).order_by('-collection_date')
    
    # Get blood inventory summary
    blood_units = BloodUnit.objects.all()
    available_units = blood_units.filter(status='ready')
    
    # Blood type inventory for lab monitoring
    blood_type_summary = {}
    for blood_type, _ in BloodUnit.BLOOD_TYPES:
        ready_count = available_units.filter(blood_type=blood_type).count()
        testing_count = blood_units.filter(blood_type=blood_type, status='testing').count()
        blood_type_summary[blood_type] = {
            'ready': ready_count,
            'testing': testing_count,
            'total': ready_count + testing_count
        }
    
    # Get donors by blood type for screening priority
    donors_by_type = {}
    for blood_type, _ in Donor.BLOOD_TYPES:
        count = Donor.objects.filter(blood_type=blood_type, is_eligible=True).count()
        donors_by_type[blood_type] = count
    
    # Test statistics
    test_stats = {
        'pass_rate': 0,
        'total_this_month': 0,
        'avg_per_day': 0
    }
    
    if completed_tests.exists():
        # Calculate pass rate (assuming results field contains pass/fail info)
        total_completed = completed_tests.count()
        # This would need to be adjusted based on how you store test results
        test_stats['pass_rate'] = round((total_completed / (total_completed + failed_tests.count())) * 100, 1)
    
    # Monthly statistics
    first_day_month = today.replace(day=1)
    monthly_tests = all_tests.filter(test_date__date__gte=first_day_month)
    test_stats['total_this_month'] = monthly_tests.count()
    
    if today.day > 0:
        test_stats['avg_per_day'] = round(test_stats['total_this_month'] / today.day, 1)
    
    context = {
        'pending_tests': pending_tests[:10],
        'completed_tests': completed_tests[:10],
        'recent_tests': all_tests[:10],
        'total_pending': pending_tests.count(),
        'total_completed': completed_tests.count(),
        'pending_tests_count': pending_tests.count(),
        'today_tests_count': today_completed.count(),
        'total_donors_count': Donor.objects.count(),
        'blood_units_available': available_units.count(),
        'donors_needing_tests': donors_needing_tests,
        'recent_blood_units': recent_blood_units[:10],
        'blood_type_summary': blood_type_summary,
        'donors_by_type': donors_by_type,
        'failed_tests_count': failed_tests.count(),
        'in_progress_tests_count': in_progress_tests.count(),
        'test_stats': test_stats,
        'blood_inventory': recent_blood_units[:10],  # For template compatibility
    }
    
    return render(request, 'core/lab_tech_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Enhanced admin dashboard with comprehensive system overview"""
    if not is_admin(request.user):
        return redirect('home')
    
    # Get today's date for filtering
    today = timezone.now().date()
    
    # User statistics
    all_users = User.objects.all()
    total_users = all_users.count()
    verified_users = all_users.filter(is_verified=True)
    pending_verifications = all_users.filter(is_verified=False)
    
    # User type breakdown
    donors = Donor.objects.all()
    patients = Patient.objects.all()
    # Staff user type removed
    lab_techs = all_users.filter(user_type='lab_tech')
    admins = all_users.filter(user_type='admin')
    
    # Blood bank statistics
    blood_units = BloodUnit.objects.all()
    available_blood_units = blood_units.filter(status='ready')
    expired_units = blood_units.filter(status='expired')
    testing_units = blood_units.filter(status='testing')
    
    # Blood type inventory
    blood_type_inventory = {}
    low_stock_count = 0
    out_of_stock_count = 0
    
    for blood_type, _ in BloodUnit.BLOOD_TYPES:
        count = available_blood_units.filter(blood_type=blood_type).count()
        blood_type_inventory[blood_type] = count
        if count == 0:
            out_of_stock_count += 1
        elif count < 5:
            low_stock_count += 1
    
    # Hospital and appointment statistics
    hospitals = Hospital.objects.filter(is_active=True)
    appointments = Appointment.objects.all()
    today_appointments = appointments.filter(appointment_date=today)
    pending_appointments = appointments.filter(status='scheduled')
    
    # Blood requests and matches
    blood_requests = BloodRequest.objects.all()
    pending_requests = blood_requests.filter(status='pending')
    urgent_requests = blood_requests.filter(
        urgency_level__in=['high', 'emergency'],
        status__in=['pending', 'approved']
    )
    
    donor_matches = DonorPatientMatch.objects.all()
    active_matches = donor_matches.filter(status__in=['pending', 'accepted'])
    
    # Recent activity (last 7 days)
    week_ago = today - timedelta(days=7)
    recent_registrations = all_users.filter(created_at__date__gte=week_ago)
    recent_donations = blood_units.filter(collection_date__date__gte=week_ago)
    recent_requests = blood_requests.filter(created_at__date__gte=week_ago)
    
    # System health indicators
    system_alerts = []
    
    if out_of_stock_count > 0:
        system_alerts.append({
            'type': 'danger',
            'message': f'{out_of_stock_count} blood types are out of stock',
            'icon': 'fas fa-exclamation-triangle'
        })
    
    if low_stock_count > 0:
        system_alerts.append({
            'type': 'warning',
            'message': f'{low_stock_count} blood types have low stock',
            'icon': 'fas fa-exclamation-circle'
        })
    
    if urgent_requests.count() > 0:
        system_alerts.append({
            'type': 'info',
            'message': f'{urgent_requests.count()} urgent blood requests pending',
            'icon': 'fas fa-clock'
        })
    
    if pending_verifications.count() > 10:
        system_alerts.append({
            'type': 'warning',
            'message': f'{pending_verifications.count()} users awaiting verification',
            'icon': 'fas fa-user-check'
        })
    
    # Monthly growth statistics
    first_day_month = today.replace(day=1)
    monthly_registrations = all_users.filter(created_at__date__gte=first_day_month).count()
    monthly_donations = blood_units.filter(collection_date__date__gte=first_day_month).count()
    
    context = {
        'total_users': total_users,
        'total_donors': donors.count(),
        'total_patients': patients.count(),
        'total_hospitals': hospitals.count(),
        'total_blood_units': blood_units.count(),
        'recent_users': all_users.order_by('-created_at')[:5],
        
        # Enhanced statistics
        'total_users_count': total_users,
        'total_donors_count': donors.count(),
        'total_patients_count': patients.count(),
        # Staff user type removed
        'total_lab_techs_count': lab_techs.count(),
        'total_admins_count': admins.count(),
        'pending_verifications_count': pending_verifications.count(),
        
        # Blood bank statistics
        'available_blood_units': available_blood_units.count(),
        'low_stock_types_count': low_stock_count,
        'out_of_stock_types_count': out_of_stock_count,
        'blood_type_inventory': blood_type_inventory,
        'expired_units_count': expired_units.count(),
        'testing_units_count': testing_units.count(),
        
        # Activity statistics
        'today_appointments_count': today_appointments.count(),
        'pending_appointments_count': pending_appointments.count(),
        'pending_requests_count': pending_requests.count(),
        'urgent_requests_count': urgent_requests.count(),
        'active_matches_count': active_matches.count(),
        
        # Recent activity
        'recent_registrations': recent_registrations,
        'recent_donations': recent_donations,
        'recent_requests': recent_requests,
        'monthly_registrations': monthly_registrations,
        'monthly_donations': monthly_donations,
        
        # System health
        'system_alerts': system_alerts,
        'pending_verifications': pending_verifications[:10],
        'urgent_requests': urgent_requests[:5],
        
        # For template compatibility
        'recent_activity': recent_registrations[:10],
    }
    
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def manage_users(request):
    """Admin view to manage all users with profile info and delete functionality"""
    if not is_admin(request.user):
        return redirect('home')
    
    # Handle user deletion
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        if user_id and action == 'delete':
            try:
                user_to_delete = User.objects.get(id=user_id)
                if user_to_delete != request.user:  # Prevent self-deletion
                    username = user_to_delete.username
                    user_to_delete.delete()
                    messages.success(request, f'User {username} has been deleted successfully.')
                else:
                    messages.error(request, 'You cannot delete your own account.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
            return redirect('manage_users')
    
    # Get all users with their profile information
    users = User.objects.all().order_by('-last_login', '-created_at')
    
    # Add profile information for each user
    user_data = []
    for user in users:
        profile_info = {
            'user': user,
            'last_login': user.last_login,
            'date_joined': user.created_at,
            'is_verified': user.is_verified,
            'profile_complete': False,
            'additional_info': {}
        }
        
        # Get specific profile information based on user type
        if user.user_type == 'donor':
            try:
                donor = Donor.objects.get(user=user)
                profile_info['profile_complete'] = True
                profile_info['additional_info'] = {
                    'blood_type': donor.blood_type,
                    'age': donor.age,
                    'weight': donor.weight,
                    'is_eligible': donor.is_eligible,
                    'last_donation': donor.last_donation_date,
                    'total_donations': BloodUnit.objects.filter(donor=donor).count()
                }
            except Donor.DoesNotExist:
                pass
        
        elif user.user_type == 'patient':
            try:
                patient = Patient.objects.get(user=user)
                profile_info['profile_complete'] = True
                profile_info['additional_info'] = {
                    'blood_type_needed': patient.blood_type_needed,
                    'age': patient.age,
                    'urgency_level': patient.urgency_level,
                    'blood_units_needed': patient.blood_units_needed,
                    'total_requests': BloodRequest.objects.filter(patient=patient).count()
                }
            except Patient.DoesNotExist:
                pass
        
        user_data.append(profile_info)
    
    # Filter by user type if requested
    user_type_filter = request.GET.get('user_type')
    if user_type_filter:
        user_data = [u for u in user_data if u['user'].user_type == user_type_filter]
    
    # Pagination
    paginator = Paginator(user_data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'user_types': User.USER_TYPES,
        'current_filter': user_type_filter,
        'total_users': len(user_data),
    }
    
    return render(request, 'core/manage_users.html', context)

@login_required
def blood_inventory_admin(request):
    """Admin view for blood inventory showing total quantities ordered by blood type"""
    if not is_admin(request.user):
        return redirect('home')
    
    # Get blood inventory summary ordered by blood type
    inventory_data = []
    total_units = 0
    
    for blood_type, display_name in BloodUnit.BLOOD_TYPES:
        units = BloodUnit.objects.filter(blood_type=blood_type)
        
        ready_count = units.filter(status='ready').count()
        testing_count = units.filter(status='testing').count()
        reserved_count = units.filter(status='reserved').count()
        used_count = units.filter(status='used').count()
        expired_count = units.filter(status='expired').count()
        rejected_count = units.filter(status='rejected').count()
        
        total_type_units = ready_count + testing_count + reserved_count
        total_units += total_type_units
        
        # Calculate total quantity in ml
        total_ml = units.aggregate(total=models.Sum('quantity_ml'))['total'] or 0
        ready_ml = units.filter(status='ready').aggregate(total=models.Sum('quantity_ml'))['total'] or 0
        
        # Determine stock status
        if ready_count == 0:
            status = 'out_of_stock'
            status_class = 'danger'
        elif ready_count < 5:
            status = 'low_stock'
            status_class = 'warning'
        elif ready_count < 10:
            status = 'moderate'
            status_class = 'info'
        else:
            status = 'good'
            status_class = 'success'
        
        inventory_data.append({
            'blood_type': blood_type,
            'display_name': display_name,
            'ready': ready_count,
            'testing': testing_count,
            'reserved': reserved_count,
            'used': used_count,
            'expired': expired_count,
            'rejected': rejected_count,
            'total_active': total_type_units,
            'total_ml': total_ml,
            'ready_ml': ready_ml,
            'status': status,
            'status_class': status_class,
        })
    
    # Sort by blood type (A+, A-, B+, B-, AB+, AB-, O+, O-)
    blood_type_order = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    inventory_data.sort(key=lambda x: blood_type_order.index(x['blood_type']))
    
    # Get recent activity
    recent_collections = BloodUnit.objects.filter(
        collection_date__gte=timezone.now() - timedelta(days=7)
    ).order_by('-collection_date')[:10]
    
    # Get low stock alerts
    low_stock_types = [item for item in inventory_data if item['status'] in ['out_of_stock', 'low_stock']]
    
    context = {
        'inventory_data': inventory_data,
        'total_units': total_units,
        'recent_collections': recent_collections,
        'low_stock_types': low_stock_types,
        'blood_statuses': BloodUnit.STATUS_CHOICES,
    }
    
    return render(request, 'core/blood_inventory_admin.html', context)

@login_required
def appointments_admin(request):
    """Admin view to display and manage all appointments"""
    if not is_admin(request.user):
        return redirect('home')
    
    # Handle appointment actions
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        action = request.POST.get('action')
        
        if appointment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                
                if action == 'delete':
                    appointment.delete()
                    messages.success(request, 'Appointment deleted successfully.')
                elif action in ['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']:
                    appointment.status = action
                    appointment.save()
                    messages.success(request, f'Appointment status updated to {action}.')
                    
            except Appointment.DoesNotExist:
                messages.error(request, 'Appointment not found.')
            
            return redirect('appointments_admin')
    
    # Get all appointments
    appointments = Appointment.objects.all().select_related(
        'donor__user', 'blood_bank__hospital'
    ).order_by('-appointment_date', '-appointment_time')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Filter by date range if requested
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    # Get statistics
    today = timezone.now().date()
    stats = {
        'total_appointments': appointments.count(),
        'today_appointments': appointments.filter(appointment_date=today).count(),
        'upcoming_appointments': appointments.filter(
            appointment_date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).count(),
        'completed_appointments': appointments.filter(status='completed').count(),
        'cancelled_appointments': appointments.filter(status='cancelled').count(),
    }
    
    # Pagination
    paginator = Paginator(appointments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'appointments': page_obj,
        'stats': stats,
        'status_choices': Appointment.STATUS_CHOICES,
        'current_status_filter': status_filter,
        'current_date_from': date_from,
        'current_date_to': date_to,
    }
    
    return render(request, 'core/appointments_admin.html', context)

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

# Blood inventory view moved to admin functionality

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

# Appointments management moved to admin functionality

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

# -------------------------
# Additional Dashboard Functionality Views
# -------------------------

@login_required
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics (AJAX updates)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    stats = {}
    
    if request.user.user_type == 'donor':
        try:
            donor = Donor.objects.get(user=request.user)
            stats = {
                'total_donations': BloodUnit.objects.filter(donor=donor).count(),
                'upcoming_appointments': Appointment.objects.filter(
                    donor=donor,
                    appointment_date__gte=timezone.now().date(),
                    status__in=['scheduled', 'confirmed']
                ).count(),
                'pending_matches': DonorPatientMatch.objects.filter(
                    donor=donor, 
                    status='pending'
                ).count(),
            }
        except Donor.DoesNotExist:
            stats = {'error': 'Donor profile not found'}
    
    elif request.user.user_type == 'patient':
        try:
            patient = Patient.objects.get(user=request.user)
            stats = {
                'blood_requests': BloodRequest.objects.filter(patient=patient).count(),
                'active_matches': DonorPatientMatch.objects.filter(
                    patient=patient,
                    status__in=['pending', 'accepted']
                ).count(),
                'available_units': BloodUnit.objects.filter(
                    blood_type=patient.blood_type_needed,
                    status='ready'
                ).count(),
            }
        except Patient.DoesNotExist:
            stats = {'error': 'Patient profile not found'}
    
    # Staff functionality removed
    
    elif request.user.user_type == 'lab_tech':
        stats = {
            'pending_tests': BloodTest.objects.filter(status='pending').count(),
            'today_completed': BloodTest.objects.filter(
                test_date__date=timezone.now().date(),
                status='completed'
            ).count(),
            'testing_units': BloodUnit.objects.filter(status='testing').count(),
        }
    
    elif request.user.user_type == 'admin':
        stats = {
            'total_users': User.objects.count(),
            'pending_verifications': User.objects.filter(is_verified=False).count(),
            'urgent_requests': BloodRequest.objects.filter(
                urgency_level__in=['high', 'emergency'],
                status__in=['pending', 'approved']
            ).count(),
            'system_alerts': BloodUnit.objects.filter(status='expired').count(),
        }
    
    return JsonResponse(stats)

@login_required 
def quick_actions_api(request):
    """API for quick actions based on user role"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    action = request.POST.get('action')
    
    # Staff functionality removed
    
    if request.user.user_type == 'lab_tech' and action == 'quick_test_update':
        test_id = request.POST.get('test_id')
        status = request.POST.get('status')
        try:
            test = BloodTest.objects.get(id=test_id)
            test.status = status
            test.save()
            return JsonResponse({'success': True, 'message': f'Test status updated to {status}'})
        except BloodTest.DoesNotExist:
            return JsonResponse({'error': 'Test not found'}, status=404)
    
    elif request.user.user_type == 'admin' and action == 'verify_user':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            user.is_verified = True
            user.save()
            return JsonResponse({'success': True, 'message': f'User {user.username} verified'})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid action or insufficient permissions'}, status=400)

@login_required
def blood_inventory_summary(request):
    """Detailed blood inventory summary for admins and lab techs"""
    if not (is_admin(request.user) or is_lab_tech(request.user)):
        return JsonResponse({'error': 'Insufficient permissions'}, status=403)
    
    inventory = {}
    total_units = 0
    
    for blood_type, display_name in BloodUnit.BLOOD_TYPES:
        units = BloodUnit.objects.filter(blood_type=blood_type)
        ready_count = units.filter(status='ready').count()
        testing_count = units.filter(status='testing').count()
        expired_count = units.filter(status='expired').count()
        
        total_type_units = ready_count + testing_count
        total_units += total_type_units
        
        # Determine status
        if ready_count == 0:
            status = 'out_of_stock'
            status_class = 'danger'
        elif ready_count < 5:
            status = 'low_stock'
            status_class = 'warning'
        elif ready_count < 10:
            status = 'moderate'
            status_class = 'info'
        else:
            status = 'good'
            status_class = 'success'
        
        inventory[blood_type] = {
            'display_name': display_name,
            'ready': ready_count,
            'testing': testing_count,
            'expired': expired_count,
            'total': total_type_units,
            'status': status,
            'status_class': status_class,
        }
    
    return JsonResponse({
        'inventory': inventory,
        'total_units': total_units,
        'timestamp': timezone.now().isoformat()
    })

@login_required
def emergency_alerts(request):
    """Get emergency alerts for the system"""
    if not is_admin(request.user):
        return JsonResponse({'error': 'Insufficient permissions'}, status=403)
    
    alerts = []
    
    # Critical blood shortages
    for blood_type, display_name in BloodUnit.BLOOD_TYPES:
        count = BloodUnit.objects.filter(blood_type=blood_type, status='ready').count()
        if count == 0:
            alerts.append({
                'type': 'critical',
                'message': f'CRITICAL: {display_name} blood type is out of stock',
                'icon': 'fas fa-exclamation-triangle',
                'timestamp': timezone.now().isoformat()
            })
        elif count < 3:
            alerts.append({
                'type': 'warning',
                'message': f'WARNING: {display_name} blood type has only {count} units remaining',
                'icon': 'fas fa-exclamation-circle',
                'timestamp': timezone.now().isoformat()
            })
    
    # Urgent blood requests
    urgent_requests = BloodRequest.objects.filter(
        urgency_level='emergency',
        status__in=['pending', 'approved']
    )
    
    for request in urgent_requests:
        alerts.append({
            'type': 'urgent',
            'message': f'EMERGENCY: Patient needs {request.blood_type_needed} blood urgently',
            'icon': 'fas fa-heartbeat',
            'timestamp': request.created_at.isoformat(),
            'patient_id': request.patient.id
        })
    
    # Expired blood units
    expired_count = BloodUnit.objects.filter(status='expired').count()
    if expired_count > 0:
        alerts.append({
            'type': 'info',
            'message': f'INFO: {expired_count} blood units have expired and need disposal',
            'icon': 'fas fa-clock',
            'timestamp': timezone.now().isoformat()
        })
    
    return JsonResponse({'alerts': alerts, 'count': len(alerts)})
