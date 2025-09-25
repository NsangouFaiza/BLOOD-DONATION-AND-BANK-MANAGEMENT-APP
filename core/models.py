from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
import uuid

class User(AbstractUser):
    """Custom user model with role-based access"""
    USER_TYPES = [
        ('donor', 'Donor'),
        ('patient', 'Patient'),
        ('staff', 'Blood Bank Staff'),
        ('lab_tech', 'Lab Technician'),
        ('admin', 'Administrator'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone = models.CharField(max_length=15, validators=[
        RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    ])
    city = models.CharField(max_length=100, blank=True, null=True)
    national_id = models.CharField(max_length=20, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Fix related_name conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='bloodbank_user_set',
        related_query_name='bloodbank_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='bloodbank_user_set',
        related_query_name='bloodbank_user',
    )

    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"

class Hospital(models.Model):
    """Hospital information"""
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    # Geolocation for maps and nearby search
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class BloodBank(models.Model):
    """Blood bank information"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.hospital.name}"

class Donor(models.Model):
    """Donor profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    BLOOD_TYPES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Height in cm")
    medical_conditions = models.TextField(blank=True)
    preferred_hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    last_donation_date = models.DateField(null=True, blank=True)
    is_eligible = models.BooleanField(default=False)
    health_status = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.blood_type}"

class Patient(models.Model):
    """Patient profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    BLOOD_TYPES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    blood_type_needed = models.CharField(max_length=3, choices=BLOOD_TYPES)
    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Height in cm")
    urgency_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    ])
    blood_units_needed = models.PositiveIntegerField(default=1)
    medical_condition = models.TextField(blank=True)
    preferred_hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    additional_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Needs {self.blood_type_needed}"

class BloodUnit(models.Model):
    """Individual blood unit information"""
    BLOOD_TYPES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    STATUS_CHOICES = [
        ('collected', 'Collected'),
        ('testing', 'Testing'),
        ('ready', 'Ready for Use'),
        ('reserved', 'Reserved'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]
    
    # Use UUIDField to ensure proper storage and uniqueness of unit identifiers
    unit_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, null=True, blank=True)
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE)
    collection_date = models.DateTimeField()
    expiry_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='collected')
    quantity_ml = models.PositiveIntegerField(default=450)  # Standard blood bag
    test_results = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.unit_id} - {self.blood_type} - {self.status}"

class Appointment(models.Model):
    """Donor appointment scheduling"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.donor.user.username} - {self.appointment_date} {self.appointment_time}"

class BloodRequest(models.Model):
    """Patient blood requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('fulfilled', 'Fulfilled'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    FULFILLMENT_TYPE = [
        ('donor_match', 'Donor Match'),
        ('blood_bank', 'Blood Bank'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    blood_type_needed = models.CharField(max_length=3, choices=Donor.BLOOD_TYPES)
    quantity_units = models.PositiveIntegerField(default=1)
    urgency_level = models.CharField(max_length=20, choices=Patient.urgency_level.field.choices)
    hospital_preference = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    fulfillment_type = models.CharField(max_length=20, choices=FULFILLMENT_TYPE, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.user.username} - {self.blood_type_needed} - {self.status}"

class DonorPatientMatch(models.Model):
    """Matching between donors and patients"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    blood_request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    donor_response = models.TextField(blank=True)
    patient_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.donor.user.username} ↔ {self.patient.user.username}"

class BloodTest(models.Model):
    """Blood test results"""
    TEST_TYPES = [
        ('pre_donation', 'Pre-Donation'),
        ('post_collection', 'Post-Collection'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    blood_unit = models.ForeignKey(BloodUnit, on_delete=models.CASCADE, null=True, blank=True)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, null=True, blank=True)
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    test_date = models.DateTimeField(auto_now_add=True)
    results = models.TextField(blank=True)
    lab_technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.test_type} - {self.status}"

class OTPVerification(models.Model):
    """OTP verification for user registration"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.otp_code}"

class Notification(models.Model):
    """System notifications"""
    NOTIFICATION_TYPES = [
        ('appointment', 'Appointment'),
        ('blood_request', 'Blood Request'),
        ('donor_match', 'Donor Match'),
        ('test_result', 'Test Result'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=[('low','Low'),('medium','Medium'),('high','High')], default='medium')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

# Community Campaigns for donation outreach
class Campaign(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# Transfusion reporting to track usage of blood units
class TransfusionReport(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    blood_unit = models.ForeignKey(BloodUnit, on_delete=models.SET_NULL, null=True, blank=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    outcome = models.CharField(max_length=100, choices=[
        ('successful', 'Successful'),
        ('complication', 'Complication'),
        ('failed', 'Failed'),
    ], default='successful')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transfusion for {self.patient.user.username} - {self.outcome}"
