from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify-otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    
    # Profile completion
    path('complete-donor-profile/', views.complete_donor_profile, name='complete_donor_profile'),
    path('complete-patient-profile/', views.complete_patient_profile, name='complete_patient_profile'),
    
    # Dashboard URLs
    path('donor-dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('patient-dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('lab-tech-dashboard/', views.lab_tech_dashboard, name='lab_tech_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Donor functionality
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    
    # Patient functionality
    path('request-blood/', views.request_blood, name='request_blood'),
    path('view-donors/', views.view_donors, name='view_donors'),
    
    # Staff functionality
    path('view-blood-inventory/', views.view_blood_inventory, name='view_blood_inventory'),
    path('manage-appointments/', views.manage_appointments, name='manage_appointments'),
    
    # Lab technician functionality
    path('record-blood-test/', views.record_blood_test, name='record_blood_test'),
    
    # Common functionality
    path('donor-patient-matches/', views.donor_patient_matches, name='donor_patient_matches'),
    path('search-donors/', views.search_donors, name='search_donors'),
    path('user-profile/', views.user_profile, name='user_profile'),
    path('notifications/', views.notifications, name='notifications'),

    # Community & Maps
    path('campaigns/', views.campaigns, name='campaigns'),
    path('hospitals-map/', views.hospitals_map, name='hospitals_map'),

    # JSON APIs
    path('api/hospitals/', views.api_hospitals, name='api_hospitals'),
    path('api/inventory/', views.api_inventory, name='api_inventory'),
    
    # Dashboard APIs
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/quick-actions/', views.quick_actions_api, name='quick_actions_api'),
    path('api/blood-inventory/', views.blood_inventory_summary, name='blood_inventory_summary'),
    path('api/emergency-alerts/', views.emergency_alerts, name='emergency_alerts'),
]
