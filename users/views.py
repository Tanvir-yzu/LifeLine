from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import (
    CreateView, UpdateView, DetailView, ListView, 
    TemplateView, DeleteView, FormView
)
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from .models import User, BloodRequest, BloodRequestResponse, UserProfile
from .forms import (
    UserRegistrationForm, UserLoginForm, BloodRequestForm, 
    UserProfileForm, BloodRequestResponseForm
)
import uuid


class HomeView(TemplateView):
    """Home page view"""
    template_name = 'users/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_requests'] = BloodRequest.objects.filter(
            status='ACTIVE', is_public=True
        ).order_by('-created_at')[:6]
        context['total_users'] = User.objects.filter(is_email_verified=True).count()
        context['active_requests'] = BloodRequest.objects.filter(status='ACTIVE').count()
        return context


class UserRegistrationView(CreateView):
    """User registration view with email verification"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:registration_success')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.is_email_verified = False
        user.email_verification_token = uuid.uuid4()
        user.email_verification_sent_at = timezone.now()
        user.save()
        
        # Send verification email
        self.send_verification_email(user)
        
        messages.success(
            self.request, 
            'Registration successful! Please check your email to verify your account.'
        )
        return super().form_valid(form)
    
    def send_verification_email(self, user):
        """Send email verification link"""
        verification_url = self.request.build_absolute_uri(
            reverse('users:verify_email', kwargs={'token': user.email_verification_token})
        )
        
        subject = 'Verify your LifeLine account'
        message = f'''
        Hi {user.get_full_name()},
        
        Thank you for registering with LifeLine Blood Bank!
        
        Please click the link below to verify your email address:
        {verification_url}
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        LifeLine Team
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


class EmailVerificationView(TemplateView):
    """Email verification view"""
    template_name = 'users/email_verified.html'
    
    def get(self, request, token):
        try:
            user = User.objects.get(email_verification_token=token)
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save()
                messages.success(request, 'Email verified successfully! You can now log in.')
            else:
                messages.info(request, 'Email already verified.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid verification token.')
        
        return render(request, self.template_name)


class UserLoginView(FormView):
    """User login view"""
    form_class = UserLoginForm
    template_name = 'users/login.html'
    success_url = reverse_lazy('users:dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users to dashboard
        if request.user.is_authenticated:
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data.get('remember_me', False)
        
        user = authenticate(self.request, username=email, password=password)
        
        if user is not None:
            if user.is_email_verified:
                login(self.request, user)
                
                # Set session expiry based on remember me
                if not remember_me:
                    self.request.session.set_expiry(0)  # Browser session
                else:
                    self.request.session.set_expiry(1209600)  # 2 weeks
                
                messages.success(self.request, f'Welcome back, {user.get_full_name()}!')
                
                # Redirect to next page if specified
                next_page = self.request.GET.get('next')
                if next_page:
                    return HttpResponseRedirect(next_page)
                
                return super().form_valid(form)
            else:
                messages.error(
                    self.request, 
                    'Please verify your email address before logging in.'
                )
        else:
            messages.error(self.request, 'Invalid email or password.')
        
        return self.form_invalid(form)


class UserLogoutView(TemplateView):
    """User logout view"""
    template_name = 'users/logout.html'
    
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return super().get(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard view"""
    template_name = 'users/dashboard.html'
    login_url = reverse_lazy('users:login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # User's blood requests
        context['my_requests'] = BloodRequest.objects.filter(
            requester=user
        ).order_by('-created_at')[:5]
        
        # Blood requests user can respond to
        context['available_requests'] = BloodRequest.objects.filter(
            status='ACTIVE',
            is_public=True
        ).exclude(
            requester=user
        ).filter(
            blood_group_needed=user.blood_group
        ).order_by('-created_at')[:5]
        
        # User's responses
        context['my_responses'] = BloodRequestResponse.objects.filter(
            donor=user
        ).order_by('-responded_at')[:5]
        
        # Statistics
        context['total_requests'] = BloodRequest.objects.filter(requester=user).count()
        context['total_responses'] = BloodRequestResponse.objects.filter(donor=user).count()
        context['can_donate'] = user.can_donate()
        context['is_eligible'] = user.is_eligible_donor()
        
        return context


class UserProfileView(LoginRequiredMixin, DetailView):
    """User profile detail view"""
    model = User
    template_name = 'profile/profile.html'
    context_object_name = 'profile_user'
    login_url = reverse_lazy('users:login')
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk:
            return get_object_or_404(User, pk=pk, is_email_verified=True)
        return self.request.user


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """User profile update view"""
    model = User
    form_class = UserProfileForm
    template_name = 'profile/profile_edit.html'
    login_url = reverse_lazy('users:login')
    
    def get_object(self):
        return self.request.user
    
    def get_success_url(self):
        messages.success(self.request, 'Profile updated successfully!')
        return reverse('users:profile')


class BloodRequestCreateView(LoginRequiredMixin, CreateView):
    """Create blood request view"""
    model = BloodRequest
    form_class = BloodRequestForm
    template_name = 'blood/blood_request_create.html'
    login_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        form.instance.requester = self.request.user
        messages.success(self.request, 'Blood request created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('users:blood_request_detail', kwargs={'pk': self.object.pk})


class BloodRequestDetailView(DetailView):
    """Blood request detail view"""
    model = BloodRequest
    template_name = 'blood/blood_request_detail.html'
    context_object_name = 'blood_request'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blood_request = self.get_object()
        
        # Check if current user can respond
        if self.request.user.is_authenticated:
            context['can_respond'] = blood_request.can_accept(self.request.user)
            
            # Check if user already responded
            context['user_response'] = BloodRequestResponse.objects.filter(
                blood_request=blood_request,
                donor=self.request.user
            ).first()
        
        # Get responses (only for requester)
        if (self.request.user.is_authenticated and 
            self.request.user == blood_request.requester):
            context['responses'] = BloodRequestResponse.objects.filter(
                blood_request=blood_request
            ).order_by('-responded_at')
        
        return context


class BloodRequestUpdateView(LoginRequiredMixin, UpdateView):
    """Update blood request view"""
    model = BloodRequest
    form_class = BloodRequestForm
    template_name = 'blood/blood_request_edit.html'
    login_url = reverse_lazy('users:login')
    
    def get_queryset(self):
        return BloodRequest.objects.filter(requester=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Blood request updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('users:blood_request_detail', kwargs={'pk': self.object.pk})


class BloodRequestDeleteView(LoginRequiredMixin, DeleteView):
    """Delete blood request view"""
    model = BloodRequest
    template_name = 'blood/blood_request_delete.html'
    success_url = reverse_lazy('users:dashboard')
    login_url = reverse_lazy('users:login')
    
    def get_queryset(self):
        return BloodRequest.objects.filter(requester=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Blood request deleted successfully!')
        return super().delete(request, *args, **kwargs)


class BloodRequestListView(ListView):
    """List all public blood requests"""
    model = BloodRequest
    template_name = 'blood/blood_request_list.html'
    context_object_name = 'blood_requests'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = BloodRequest.objects.filter(
            status='ACTIVE',
            is_public=True
        ).order_by('-created_at')
        
        # Filter by blood group
        blood_group = self.request.GET.get('blood_group')
        if blood_group:
            queryset = queryset.filter(blood_group_needed=blood_group)
        
        # Filter by urgency
        urgency = self.request.GET.get('urgency')
        if urgency:
            queryset = queryset.filter(urgency=urgency)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(patient_name__icontains=search) |
                Q(hospital_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blood_groups'] = User.BLOOD_GROUP_CHOICES
        context['urgency_levels'] = BloodRequest.URGENCY_CHOICES
        context['current_filters'] = {
            'blood_group': self.request.GET.get('blood_group', ''),
            'urgency': self.request.GET.get('urgency', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        # Add statistics for the dashboard
        context['total_requests'] = BloodRequest.objects.filter(is_public=True).count()
        context['active_requests'] = BloodRequest.objects.filter(status='ACTIVE', is_public=True).count()
        context['urgent_requests'] = BloodRequest.objects.filter(
            status='ACTIVE', 
            is_public=True, 
            urgency__in=['HIGH', 'CRITICAL']
        ).count()
        context['fulfilled_requests'] = BloodRequest.objects.filter(status='FULFILLED', is_public=True).count()
        
        return context
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blood_groups'] = User.BLOOD_GROUP_CHOICES
        context['urgency_levels'] = BloodRequest.URGENCY_CHOICES
        context['current_filters'] = {
            'blood_group': self.request.GET.get('blood_group', ''),
            'urgency': self.request.GET.get('urgency', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context


class BloodRequestResponseCreateView(LoginRequiredMixin, CreateView):
    """Respond to blood request view"""
    model = BloodRequestResponse
    form_class = BloodRequestResponseForm
    template_name = 'blood/blood_request_respond.html'
    login_url = reverse_lazy('users:login')
    
    def dispatch(self, request, *args, **kwargs):
        self.blood_request = get_object_or_404(BloodRequest, pk=kwargs['pk'])
        
        # Check if user can respond
        if not self.blood_request.can_accept(request.user):
            messages.error(request, 'You cannot respond to this blood request.')
            return redirect('users:blood_request_detail', pk=self.blood_request.pk)
        
        # Check if user already responded
        if BloodRequestResponse.objects.filter(
            blood_request=self.blood_request,
            donor=request.user
        ).exists():
            messages.info(request, 'You have already responded to this request.')
            return redirect('users:blood_request_detail', pk=self.blood_request.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.blood_request = self.blood_request
        form.instance.donor = self.request.user
        
        messages.success(
            self.request, 
            'Your response has been sent to the requester!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('users:blood_request_detail', kwargs={'pk': self.blood_request.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blood_request'] = self.blood_request
        return context
    

class BloodRequestResponseListView(ListView):
    """List all blood request responses"""
    model = BloodRequestResponse
    template_name = 'blood/bloodrequestresponse_list.html'
    context_object_name = 'responses'
    paginate_by = 12

    def get_queryset(self):
        queryset = BloodRequestResponse.objects.select_related(
            'blood_request', 'donor'
        ).order_by('-responded_at')

        # Filtering
        blood_group = self.request.GET.get('blood_group')
        if blood_group:
            queryset = queryset.filter(blood_request__blood_group_needed=blood_group)

        urgency = self.request.GET.get('urgency')
        if urgency:
            queryset = queryset.filter(blood_request__urgency=urgency)

        response_status = self.request.GET.get('response')
        if response_status:
            queryset = queryset.filter(response=response_status)

        # Searching
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(donor__full_name__icontains=search_query) |
                Q(blood_request__patient_name__icontains=search_query) |
                Q(blood_request__hospital_name__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blood_groups'] = User.BLOOD_GROUP_CHOICES
        context['urgency_levels'] = BloodRequest.URGENCY_CHOICES
        context['response_statuses'] = BloodRequestResponse.RESPONSE_CHOICES
        context['current_filters'] = {
            'blood_group': self.request.GET.get('blood_group', ''),
            'urgency': self.request.GET.get('urgency', ''),
            'response': self.request.GET.get('response', ''),
            'search': self.request.GET.get('search', ''),
        }

        # Statistics
        context['total_responses'] = BloodRequestResponse.objects.count()
        context['accepted_responses'] = BloodRequestResponse.objects.filter(response='ACCEPTED').count()
        context['completed_responses'] = BloodRequestResponse.objects.filter(response='COMPLETED').count()
        context['declined_responses'] = BloodRequestResponse.objects.filter(response='DECLINED').count()

        return context


class MyBloodRequestsView(LoginRequiredMixin, ListView):
    """User's blood requests view"""
    model = BloodRequest
    template_name = 'blood/my_blood_requests.html'
    context_object_name = 'blood_requests'
    paginate_by = 10
    login_url = reverse_lazy('users:login')
    
    def get_queryset(self):
        return BloodRequest.objects.filter(
            requester=self.request.user
        ).order_by('-created_at')


class MyResponsesView(LoginRequiredMixin, ListView):
    """User's blood request responses view"""
    model = BloodRequestResponse
    template_name = 'blood/my_responses.html'
    context_object_name = 'responses'
    paginate_by = 10
    login_url = reverse_lazy('users:login')
    
    def get_queryset(self):
        return BloodRequestResponse.objects.filter(
            donor=self.request.user
        ).order_by('-responded_at')


class DonorSearchView(ListView):
    """Search for donors view"""
    model = User
    template_name = 'blood/donor_search.html'
    context_object_name = 'donors'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = User.objects.filter(
            is_email_verified=True,
            is_donor=True,
            is_available_for_donation=True
        ).order_by('?')  # Random order
        
        # Filter by blood group
        blood_group = self.request.GET.get('blood_group')
        if blood_group:
            queryset = queryset.filter(blood_group=blood_group)
        
        # Filter by location (address contains)
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(address__icontains=location)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blood_groups'] = User.BLOOD_GROUP_CHOICES
        context['current_filters'] = {
            'blood_group': self.request.GET.get('blood_group', ''),
            'location': self.request.GET.get('location', ''),
        }
        return context


class RegistrationSuccessView(TemplateView):
    """Registration success page"""
    template_name = 'users/registration_success.html'


# AJAX Views
def check_email_availability(request):
    """AJAX view to check email availability"""
    email = request.GET.get('email')
    is_available = not User.objects.filter(email=email).exists()
    return JsonResponse({'available': is_available})


@login_required
def update_donation_status(request):
    """AJAX view to update donation availability status"""
    if request.method == 'POST':
        status = request.POST.get('status') == 'true'
        request.user.is_available_for_donation = status
        request.user.save()
        return JsonResponse({'success': True, 'status': status})
    return JsonResponse({'success': False})