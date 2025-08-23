from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User, BloodRequest, BloodRequestResponse, UserProfile
from datetime import date, timedelta


class UserRegistrationForm(UserCreationForm):
    """Custom user registration form with additional fields"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name (will be used as username)'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+880XXXXXXXXX'
        })
    )
    
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    blood_group = forms.ChoiceField(
        choices=[('', 'Select Blood Group')] + User.BLOOD_GROUP_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    city = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    weight = forms.FloatField(
        required=False,
        min_value=30,
        max_value=200,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Weight in kg (optional)'
        })
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'gender', 'blood_group', 'weight',
            'password1', 'password2'
        ]
        widgets = {
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirm Password'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if User.objects.filter(username=first_name).exists():
            raise ValidationError("A user with this name already exists. Please choose a different first name.")
        return first_name
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                raise ValidationError("You must be at least 16 years old to register.")
            if age > 65:
                raise ValidationError("Age must be realistic.")
        return dob
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValidationError("Please enter a valid phone number.")
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['first_name']  # Use first_name as username
        user.email = self.cleaned_data['email']
        user.address = self.cleaned_data['city']  # Map city to address field
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """Custom login form with Tailwind CSS styling"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'pl-10 pr-3 py-2 w-full border rounded-lg focus:ring-2 focus:ring-red-400 focus:outline-none',
            'placeholder': 'your@email.com',
            'required': True,
            'id': 'email'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'pl-10 pr-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-red-400 focus:outline-none',
            'placeholder': '••••••••',
            'required': True,
            'id': 'password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded',
            'id': 'remember_me'
        }),
        label='Remember me'
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            from django.contrib.auth import authenticate
            from .models import User
            
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    raise forms.ValidationError('This account is inactive.')
                if not user.is_email_verified:
                    raise forms.ValidationError('Please verify your email address before logging in.')
                    
                # Authenticate user
                user = authenticate(username=email, password=password)
                if not user:
                    raise forms.ValidationError('Invalid email or password.')
                    
            except User.DoesNotExist:
                raise forms.ValidationError('Invalid email or password.')
                
        return cleaned_data


class BloodRequestForm(forms.ModelForm):
    """Form for creating blood requests"""
    
    class Meta:
        model = BloodRequest
        fields = [
            'patient_name', 'blood_group_needed', 'units_needed',
            'hospital_name', 'hospital_address', 'urgency', 
            'needed_by_date', 'description', 'contact_phone', 'is_public'
        ]
        widgets = {
            'patient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Patient Name'
            }),
            'blood_group_needed': forms.Select(attrs={'class': 'form-control'}),
            'units_needed': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'hospital_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hospital Name'
            }),
            'hospital_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Hospital Address'
            }),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'needed_by_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional details about the blood requirement...'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact Phone Number'
            }),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_needed_by_date(self):
        needed_by = self.cleaned_data.get('needed_by_date')
        if needed_by and needed_by <= timezone.now():
            raise ValidationError("The needed by date must be in the future.")
        return needed_by


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'gender', 'blood_group', 'weight', 'address', 
            'last_donation_date', 'medical_conditions',
            'is_available_for_donation'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'last_donation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any medical conditions or medications...'
            }),
            'is_available_for_donation': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_last_donation_date(self):
        last_donation = self.cleaned_data.get('last_donation_date')
        if last_donation and last_donation > date.today():
            raise ValidationError("Last donation date cannot be in the future.")
        return last_donation


class BloodRequestResponseForm(forms.ModelForm):
    """Form for responding to blood requests"""
    
    class Meta:
        model = BloodRequestResponse
        fields = [
            'response', 'message', 'donor_phone', 'preferred_contact_time'
        ]
        widgets = {
            'response': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional message to the requester...'
            }),
            'donor_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your contact phone number'
            }),
            'preferred_contact_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Best time to contact you (e.g., 9 AM - 5 PM)'
            })
        }