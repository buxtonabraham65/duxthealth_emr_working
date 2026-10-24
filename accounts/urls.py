from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # Auth and signup views
    path('signup/', views.access_request, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Access request status and thank you
    path('thank-you/', views.thank_you, name='thank_you'),
    path('request-status/', views.request_status_view, name='request_status'),

    # Admin review & approval
    path('admin/requests/', views.review_access_requests, name='review_access_requests'),
    path('admin/requests/approve/<int:request_id>/', views.approve_request, name='approve_request'),

    # Password management (secured with login_required)
    path('accounts/change-password/', login_required(auth_views.PasswordChangeView.as_view(
        template_name='accounts/change_password.html',
        success_url='/accounts/password-changed/'
    )), name='password_change'),

    path('accounts/password-changed/', login_required(auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_changed.html'
    )), name='password_change_done'),
]
