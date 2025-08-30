from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import *
from django.utils import timezone

class UserRegistrationForm(UserCreationForm):
    """Form for user registration with OTP verification"""
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    national_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your national ID'
        })
    )
    id_card_image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'national_id', 'id_card_image', 'user_type', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your last name'}),
        }

class OTPVerificationForm(forms.Form):
    """Form for OTP verification"""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit OTP',
            'maxlength': '6'
        })
    )

class DonorProfileForm(forms.ModelForm):
    """Form for donor profile completion"""
    class Meta:
        model = Donor
        fields = ('blood_type', 'age', 'weight', 'height', 'medical_conditions', 'last_donation_date', 'preferred_hospital', 'emergency_contact')
        widgets = {
            'blood_type': forms.Select(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Your age', 'min': 18, 'max': 65}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight in kg', 'min': 50, 'max': 300}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Height in cm', 'min': 100, 'max': 250}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any medical conditions, medications, or allergies'}),
            'last_donation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'preferred_hospital': forms.Select(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact phone number'}),
        }

class PatientProfileForm(forms.ModelForm):
    """Form for patient profile completion"""
    class Meta:
        model = Patient
        fields = ('blood_type_needed', 'age', 'weight', 'height', 'urgency_level', 'blood_units_needed', 'medical_condition', 'preferred_hospital', 'emergency_contact', 'additional_notes')
        widgets = {
            'blood_type_needed': forms.Select(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Your age', 'min': 1, 'max': 120}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight in kg', 'min': 1, 'max': 300}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Height in cm', 'min': 50, 'max': 250}),
            'urgency_level': forms.Select(attrs={'class': 'form-control'}),
            'blood_units_needed': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of blood units needed', 'min': 1, 'max': 10}),
            'medical_condition': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your medical condition'}),
            'preferred_hospital': forms.Select(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact phone number'}),
            'additional_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any additional information'}),
        }

class AppointmentForm(forms.ModelForm):
    """Form for booking donor appointments"""
    class Meta:
        model = Appointment
        fields = ('blood_bank', 'appointment_date', 'appointment_time', 'notes')
        widgets = {
            'blood_bank': forms.Select(attrs={'class': 'form-control'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special notes or requirements?'}),
        }

    def clean_appointment_date(self):
        date = self.cleaned_data['appointment_date']
        if date < timezone.now().date():
            raise ValidationError("Appointment date cannot be in the past.")
        return date

class BloodRequestForm(forms.ModelForm):
    """Form for patient blood requests"""
    class Meta:
        model = BloodRequest
        fields = ('blood_type_needed', 'quantity_units', 'urgency_level', 'hospital_preference', 'notes')
        widgets = {
            'blood_type_needed': forms.Select(attrs={'class': 'form-control'}),
            'quantity_units': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of blood units needed', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional information about your request'}),
        }

class BloodTestForm(forms.ModelForm):
    """Form for lab technicians to record blood test results"""
    class Meta:
        model = BloodTest
        exclude = ['test_date']  # Exclude test_date as it's auto-populated
        fields = ('donor', 'test_type', 'status', 'results', 'notes')
        widgets = {
            'donor': forms.Select(attrs={'class': 'form-control'}),
            'test_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'results': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter test results and findings'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes or observations'}),
        }

class BloodUnitForm(forms.ModelForm):
    """Form for blood bank staff to record blood collection"""
    class Meta:
        model = BloodUnit
        fields = ('blood_type', 'quantity_ml', 'collection_date', 'expiry_date', 'notes')
        widgets = {
            'blood_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity_ml': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Blood quantity in ml', 'min': 100, 'max': 500}),
            'collection_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'expiry_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special notes about this blood unit?'}),
        }

class DonorPatientMatchForm(forms.ModelForm):
    """Form for donor-patient communication"""
    class Meta:
        model = DonorPatientMatch
        fields = ('donor_response', 'patient_response')
        widgets = {
            'donor_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your response to the patient'}),
            'patient_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your response to the donor'}),
        }

class HospitalForm(forms.ModelForm):
    """Form for adding/editing hospitals"""
    class Meta:
        model = Hospital
        fields = ('name', 'address', 'city', 'phone', 'email')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hospital name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
        }

class BloodBankForm(forms.ModelForm):
    """Form for adding/editing blood banks"""
    class Meta:
        model = BloodBank
        fields = ('hospital', 'name', 'address', 'phone', 'email')
        widgets = {
            'hospital': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Blood bank name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Blood bank address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
        }
