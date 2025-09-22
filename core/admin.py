from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Custom admin site configuration
admin.site.site_header = "LifeLink Administration"
admin.site.site_title = "LifeLink Admin Portal"
admin.site.index_title = "Welcome to LifeLink Administration"

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'phone', 'national_id', 'is_verified', 'is_active')
    list_filter = ('user_type', 'is_verified', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone', 'national_id')
    ordering = ('-created_at',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Blood Bank Info', {
            'fields': ('user_type', 'phone', 'national_id', 'id_card_image', 'is_verified')
        }),
    )

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'hospital', 'location', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('is_active', 'start_date', 'end_date', 'hospital')
    search_fields = ('title', 'location', 'description')
    ordering = ('-start_date',)

@admin.register(TransfusionReport)
class TransfusionReportAdmin(admin.ModelAdmin):
    list_display = ('patient', 'blood_unit', 'hospital', 'outcome', 'created_at')
    list_filter = ('outcome', 'hospital', 'created_at')
    search_fields = ('patient__user__username', 'blood_unit__unit_id')
    ordering = ('-created_at',)
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Blood Bank Info', {
            'fields': ('user_type', 'phone', 'national_id', 'id_card_image')
        }),
    )

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'email', 'latitude', 'longitude', 'is_active', 'created_at')
    list_filter = ('city', 'is_active', 'created_at')
    search_fields = ('name', 'city', 'phone', 'email')
    ordering = ('name',)

@admin.register(BloodBank)
class BloodBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'hospital', 'phone', 'is_active', 'created_at')
    list_filter = ('hospital', 'is_active', 'created_at')
    search_fields = ('name', 'hospital__name', 'phone')
    ordering = ('hospital__name', 'name')

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_type', 'age', 'weight', 'is_eligible', 'last_donation_date', 'created_at')
    list_filter = ('blood_type', 'is_eligible', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'blood_type', 'age', 'weight')
        }),
        ('Donation Info', {
            'fields': ('last_donation_date', 'is_eligible', 'health_status')
        }),
    )

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_type_needed', 'urgency_level', 'preferred_hospital', 'created_at')
    list_filter = ('blood_type_needed', 'urgency_level', 'preferred_hospital', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'blood_type_needed', 'urgency_level')
        }),
        ('Medical Info', {
            'fields': ('medical_condition', 'preferred_hospital')
        }),
    )

@admin.register(BloodUnit)
class BloodUnitAdmin(admin.ModelAdmin):
    list_display = ('unit_id', 'blood_type', 'donor', 'blood_bank', 'status', 'collection_date', 'expiry_date')
    list_filter = ('blood_type', 'status', 'blood_bank', 'collection_date')
    search_fields = ('unit_id', 'donor__user__username', 'blood_bank__name')
    ordering = ('-collection_date',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('unit_id', 'blood_type', 'donor', 'blood_bank')
        }),
        ('Collection Info', {
            'fields': ('collection_date', 'expiry_date', 'quantity_ml')
        }),
        ('Status Info', {
            'fields': ('status', 'test_results', 'notes')
        }),
    )

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('donor', 'blood_bank', 'appointment_date', 'appointment_time', 'status', 'created_at')
    list_filter = ('blood_bank', 'status', 'appointment_date', 'created_at')
    search_fields = ('donor__user__username', 'blood_bank__name')
    ordering = ('-appointment_date', '-appointment_time')
    
    fieldsets = (
        ('Appointment Info', {
            'fields': ('donor', 'blood_bank', 'appointment_date', 'appointment_time')
        }),
        ('Status Info', {
            'fields': ('status', 'notes')
        }),
    )

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('patient', 'blood_type_needed', 'quantity_units', 'urgency_level', 'status', 'fulfillment_type', 'created_at')
    list_filter = ('blood_type_needed', 'urgency_level', 'status', 'fulfillment_type', 'created_at')
    search_fields = ('patient__user__username', 'patient__user__email')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Request Info', {
            'fields': ('patient', 'blood_type_needed', 'quantity_units', 'urgency_level')
        }),
        ('Fulfillment Info', {
            'fields': ('hospital_preference', 'status', 'fulfillment_type', 'notes')
        }),
    )

@admin.register(DonorPatientMatch)
class DonorPatientMatchAdmin(admin.ModelAdmin):
    list_display = ('donor', 'patient', 'blood_request', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('donor__user__username', 'patient__user__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Match Info', {
            'fields': ('donor', 'patient', 'blood_request', 'status')
        }),
        ('Communication', {
            'fields': ('donor_response', 'patient_response')
        }),
    )

@admin.register(BloodTest)
class BloodTestAdmin(admin.ModelAdmin):
    list_display = ('test_type', 'donor', 'blood_unit', 'status', 'lab_technician', 'test_date')
    list_filter = ('test_type', 'status', 'test_date', 'created_at')
    search_fields = ('donor__user__username', 'blood_unit__unit_id')
    ordering = ('-test_date',)
    
    fieldsets = (
        ('Test Info', {
            'fields': ('test_type', 'donor', 'blood_unit', 'status')
        }),
        ('Results', {
            'fields': ('results', 'lab_technician', 'notes')
        }),
    )

@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'is_used', 'expires_at', 'created_at')
    list_filter = ('is_used', 'expires_at', 'created_at')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('OTP Info', {
            'fields': ('user', 'otp_code', 'is_used', 'expires_at')
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'priority', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Notification Info', {
            'fields': ('user', 'notification_type', 'title', 'message', 'is_read')
        }),
    )
