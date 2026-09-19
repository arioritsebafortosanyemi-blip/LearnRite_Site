from django.contrib.auth import views as auth_views
from django.urls import path

from reps import views

app_name = "reps"

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='reps/login.html', next_page='reps:dashboard'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='reps:login'), name='logout'),

    path('employment-verification/', views.employment_verification, name='employment_verification'),
    path('employment-verification/status/', views.employment_verification_status,
         name='employment_verification_status'),
    path('employment-verification/<int:pk>/photo/', views.employment_verification_photo,
         name='employment_verification_photo'),
    path('employment-verification/guarantor/<int:pk>/photo/', views.guarantor_photo,
         name='guarantor_photo'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('invoices/new/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/mark-paid/', views.invoice_mark_paid, name='invoice_mark_paid'),
    path('invoices/<int:pk>/invoice.pdf', views.invoice_pdf, name='invoice_pdf'),
    path('invoices/<int:pk>/internal-invoice.pdf', views.internal_invoice_pdf, name='internal_invoice_pdf'),
    path('invoices/<int:pk>/receipt.pdf', views.receipt_pdf, name='receipt_pdf'),

    path('password-reset/',
         views.PasswordResetView.as_view(
             template_name='reps/password_reset.html',
             email_template_name='reps/password_reset_email.txt',
             subject_template_name='reps/password_reset_subject.txt',
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='reps/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='reps/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='reps/password_reset_complete.html'),
         name='password_reset_complete'),
]
