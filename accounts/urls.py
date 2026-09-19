from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('verify-email/resend/', views.resend_verification_email, name='resend_verification_email'),
    path('verify-email/pending/', views.verify_email_pending, name='verify_email_pending'),
    path('setup/', views.confirm_account_setup, name='account_setup'),
    path('profile/', views.profile, name='profile'),
    path('school-verification/', views.school_verification, name='school_verification'),
    path('school-verification/status/', views.school_verification_status, name='school_verification_status'),
    path('school-verification/<int:pk>/photo/', views.school_verification_photo, name='school_verification_photo'),
    path('school-verification/<int:pk>/school-photo/', views.school_verification_school_photo,
         name='school_verification_school_photo'),
    path('school-verification/<int:pk>/<str:which>.pdf', views.school_verification_pdf, name='school_verification_pdf'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:pk>/', views.wishlist_toggle, name='wishlist_toggle'),

    path('password-reset/',
         views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.txt',
             subject_template_name='accounts/password_reset_subject.txt',
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
]
