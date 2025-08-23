from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, BloodRequest, BloodRequestResponse, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    
    list_display = (
        'email', 'get_full_name', 'blood_group', 'is_donor', 
        'is_email_verified', 'is_available_for_donation', 
        'last_donation_date', 'created_at'
    )
    
    list_filter = (
        'blood_group', 'is_donor', 'is_recipient', 'is_email_verified',
        'is_available_for_donation', 'gender', 'created_at'
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'full_name', 'phone_number')
    
    readonly_fields = (
        'email_verification_token', 'created_at', 'updated_at', 
        'last_login', 'date_joined', 'get_age_display', 'donation_eligibility'
    )
    
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'full_name', 'phone_number',
                'date_of_birth', 'gender', 'address'
            )
        }),
        ('Blood Information', {
            'fields': (
                'blood_group', 'weight', 'last_donation_date', 
                'medical_conditions', 'get_age_display', 'donation_eligibility'
            )
        }),
        ('Account Status', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'is_email_verified',
                'is_donor', 'is_recipient', 'is_available_for_donation'
            )
        }),
        ('Email Verification', {
            'fields': (
                'email_verification_token', 'email_verification_sent_at'
            ),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Required Information', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
        ('Optional Information', {
            'classes': ('wide', 'collapse'),
            'fields': (
                'full_name', 'phone_number', 'date_of_birth', 'gender',
                'blood_group', 'weight', 'address'
            ),
        }),
    )
    
    def get_age_display(self, obj):
        """Display user's age"""
        age = obj.get_age()
        if age:
            return f"{age} years"
        return "Not provided"
    get_age_display.short_description = "Age"
    
    def donation_eligibility(self, obj):
        """Display donation eligibility status"""
        if obj.is_eligible_donor():
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Eligible</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Not Eligible</span>'
        )
    donation_eligibility.short_description = "Donation Eligibility"


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    """Admin for BloodRequest model"""
    
    list_display = (
        'patient_name', 'blood_group_needed', 'units_needed', 
        'urgency', 'status', 'requester', 'hospital_name', 
        'needed_by_date', 'created_at'
    )
    
    list_filter = (
        'blood_group_needed', 'urgency', 'status', 'is_public',
        'created_at', 'needed_by_date'
    )
    
    search_fields = (
        'patient_name', 'hospital_name', 'requester__email',
        'requester__first_name', 'requester__last_name', 'description'
    )
    
    readonly_fields = ('created_at', 'updated_at', 'is_expired_display', 'compatible_donors_count')
    
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Request Information', {
            'fields': (
                'requester', 'patient_name', 'blood_group_needed', 
                'units_needed', 'description'
            )
        }),
        ('Medical Information', {
            'fields': ('hospital_name', 'hospital_address')
        }),
        ('Request Details', {
            'fields': (
                'urgency', 'needed_by_date', 'contact_phone', 
                'is_expired_display', 'compatible_donors_count'
            )
        }),
        ('Status', {
            'fields': ('status', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired_display(self, obj):
        """Display if request is expired"""
        if obj.is_expired():
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Expired</span>'
            )
        return format_html(
            '<span style="color: green; font-weight: bold;">✓ Active</span>'
        )
    is_expired_display.short_description = "Expiry Status"
    
    def compatible_donors_count(self, obj):
        """Display count of compatible donors"""
        count = obj.get_compatible_donors().count()
        return f"{count} compatible donors"
    compatible_donors_count.short_description = "Compatible Donors"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('requester')


@admin.register(BloodRequestResponse)
class BloodRequestResponseAdmin(admin.ModelAdmin):
    """Admin for BloodRequestResponse model"""
    
    list_display = (
        'donor', 'blood_request_patient', 'response', 
        'donor_phone', 'responded_at'
    )
    
    list_filter = ('response', 'responded_at')
    
    search_fields = (
        'donor__email', 'donor__first_name', 'donor__last_name',
        'blood_request__patient_name', 'message'
    )
    
    readonly_fields = ('responded_at', 'updated_at')
    
    ordering = ('-responded_at',)
    
    fieldsets = (
        ('Response Information', {
            'fields': ('blood_request', 'donor', 'response', 'message')
        }),
        ('Contact Information', {
            'fields': ('donor_phone', 'preferred_contact_time')
        }),
        ('Timestamps', {
            'fields': ('responded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def blood_request_patient(self, obj):
        """Display patient name from blood request"""
        return obj.blood_request.patient_name
    blood_request_patient.short_description = "Patient Name"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('donor', 'blood_request')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model"""
    
    list_display = (
        'user', 'total_donations', 'total_requests_fulfilled',
        'privacy_level', 'receive_email_notifications', 'created_at'
    )
    
    list_filter = (
        'privacy_level', 'receive_email_notifications', 
        'receive_sms_notifications', 'created_at'
    )
    
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name',
        'emergency_contact_name', 'emergency_contact_phone'
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relation'
            )
        }),
        ('Donation History', {
            'fields': ('total_donations', 'total_requests_fulfilled')
        }),
        ('Preferences', {
            'fields': (
                'receive_email_notifications', 'receive_sms_notifications',
                'privacy_level'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


# Customize admin site headers
admin.site.site_header = "LifeLine Blood Bank Administration"
admin.site.site_title = "LifeLine Admin"
admin.site.index_title = "Welcome to LifeLine Blood Bank Administration"