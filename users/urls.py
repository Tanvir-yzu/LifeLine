from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Home and Authentication URLs
    path('', views.HomeView.as_view(), name='home'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('registration-success/', views.RegistrationSuccessView.as_view(), name='registration_success'),
    path('verify-email/<uuid:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    
    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(
    template_name='users/password_reset.html',
    email_template_name='users/password_reset_email.txt',  # Changed from .html to .txt
    subject_template_name='users/password_reset_subject.txt',
    success_url=reverse_lazy('users:password_reset_done')
    ), name='password_reset'),
    
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    
    
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url=reverse_lazy('users:password_reset_complete')
    ), name='password_reset_confirm'),
    
    
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Dashboard and Profile URLs
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/', views.UserProfileView.as_view(), name='profile_detail'),
    path('profile/edit/', views.UserProfileUpdateView.as_view(), name='profile_edit'),
    
    # Blood Request URLs
    path('blood-requests/', views.BloodRequestListView.as_view(), name='blood_request_list'),
    path('blood-requests/create/', views.BloodRequestCreateView.as_view(), name='blood_request_create'),
    path('blood-requests/<int:pk>/', views.BloodRequestDetailView.as_view(), name='blood_request_detail'),
    path('blood-requests/<int:pk>/edit/', views.BloodRequestUpdateView.as_view(), name='blood_request_edit'),
    path('blood-requests/<int:pk>/delete/', views.BloodRequestDeleteView.as_view(), name='blood_request_delete'),
    path('blood-requests/<int:pk>/respond/', views.BloodRequestResponseCreateView.as_view(), name='blood_request_respond'),
    path('blood-request-responses/', views.BloodRequestResponseListView.as_view(), name='blood_request_response_list'),
    
    # User's Blood Requests and Responses
    path('my-requests/', views.MyBloodRequestsView.as_view(), name='my_blood_requests'),
    path('my-responses/', views.MyResponsesView.as_view(), name='my_blood_responses'),
    
    # Donor Search
    path('find-donors/', views.DonorSearchView.as_view(), name='find_donors'),
    
    # AJAX URLs
    path('ajax/check-email/', views.check_email_availability, name='check_email_availability'),
    path('ajax/update-donation-status/', views.update_donation_status, name='update_donation_status'),
]