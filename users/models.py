from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.urls import reverse
import uuid
# Signal to create UserProfile automatically when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    """Custom User model with email verification and blood donation features"""
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Basic Information
    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    # Address Information
    address = models.TextField(blank=True)
    
    # Blood Information
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    weight = models.FloatField(blank=True, null=True, help_text="Weight in kg")
    last_donation_date = models.DateField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, help_text="Any medical conditions or medications")
    
    # Account Status
    is_email_verified = models.BooleanField(default=False)
    is_donor = models.BooleanField(default=True, help_text="Can donate blood")
    is_recipient = models.BooleanField(default=True, help_text="Can receive blood")
    is_available_for_donation = models.BooleanField(default=True)
    
    # Email Verification
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # Fix for reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    class Meta:
        db_table = 'users_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        if self.full_name:
            return self.full_name
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_absolute_url(self):
        return reverse('users:profile', kwargs={'pk': self.pk})
    
    def can_donate(self):
        """Check if user can donate blood based on last donation date"""
        if not self.is_donor or not self.is_available_for_donation:
            return False
        
        if self.last_donation_date:
            # Must wait at least 3 months (90 days) between donations
            days_since_last_donation = (timezone.now().date() - self.last_donation_date).days
            return days_since_last_donation >= 90
        
        return True
    
    def get_age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def is_eligible_donor(self):
        """Check if user meets basic donor eligibility criteria"""
        age = self.get_age()
        if not age:
            return False
        
        # Basic eligibility: age 18-65, weight > 50kg
        return (
            18 <= age <= 65 and
            self.weight and self.weight >= 50 and
            self.blood_group and
            self.can_donate()
        )


class BloodRequest(models.Model):
    """Model for blood donation requests/events"""
    
    URGENCY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('FULFILLED', 'Fulfilled'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    # Request Information
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blood_requests')
    patient_name = models.CharField(max_length=200)
    blood_group_needed = models.CharField(max_length=3, choices=User.BLOOD_GROUP_CHOICES)
    units_needed = models.PositiveIntegerField(default=1, help_text="Number of blood units needed")
    
    # Medical Information
    hospital_name = models.CharField(max_length=200)
    hospital_address = models.TextField()
    
    # Request Details
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='MEDIUM')
    needed_by_date = models.DateTimeField()
    description = models.TextField(help_text="Additional details about the request")
    
    # Contact Information
    contact_phone = models.CharField(max_length=15)
    
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    is_public = models.BooleanField(default=True, help_text="Make this request visible to all users")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_blood_request'
        verbose_name = 'Blood Request'
        verbose_name_plural = 'Blood Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Blood Request for {self.patient_name} - {self.blood_group_needed} ({self.urgency})"
    
    def get_absolute_url(self):
        return reverse('users:blood_request_detail', kwargs={'pk': self.pk})
    
    def is_expired(self):
        """Check if the request has expired"""
        if self.needed_by_date is None:
            return False
        return timezone.now() > self.needed_by_date
    
    def can_accept(self, user):
        """Check if a user can accept this blood request"""
        if not user or not user.is_authenticated:
            return False
            
        return (
            user != self.requester and
            user.is_eligible_donor() and
            user.blood_group == self.blood_group_needed and
            self.status == 'ACTIVE' and
            not self.is_expired()
        )
    
    def get_compatible_donors(self):
        """Get list of compatible donors for this request"""
        return User.objects.filter(
            blood_group=self.blood_group_needed,
            is_donor=True,
            is_available_for_donation=True,
            is_email_verified=True
        ).exclude(id=self.requester.id)


class BloodRequestResponse(models.Model):
    """Model to track user responses to blood requests"""
    
    RESPONSE_CHOICES = [
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('COMPLETED', 'Completed'),
    ]
    
    blood_request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='responses')
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blood_responses')
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES)
    message = models.TextField(blank=True, help_text="Optional message from donor")
    
    # Contact Information
    donor_phone = models.CharField(max_length=15, blank=True)
    preferred_contact_time = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    responded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_blood_request_response'
        verbose_name = 'Blood Request Response'
        verbose_name_plural = 'Blood Request Responses'
        unique_together = ['blood_request', 'donor']
        ordering = ['-responded_at']
    
    def __str__(self):
        return f"{self.donor.get_full_name()} - {self.response} to {self.blood_request.patient_name}"


class UserProfile(models.Model):
    """Extended profile information for users"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    emergency_contact_relation = models.CharField(max_length=100, blank=True)
    
    # Donation History
    total_donations = models.PositiveIntegerField(default=0)
    total_requests_fulfilled = models.PositiveIntegerField(default=0)
    
    # Preferences
    receive_email_notifications = models.BooleanField(default=True)
    receive_sms_notifications = models.BooleanField(default=False)
    privacy_level = models.CharField(
        max_length=20,
        choices=[
            ('PUBLIC', 'Public'),
            ('DONORS_ONLY', 'Donors Only'),
            ('PRIVATE', 'Private'),
        ],
        default='PUBLIC'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile of {self.user.get_full_name()}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)