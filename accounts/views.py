from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import AccessRequestForm
from .models import AccessRequest
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.crypto import get_random_string

# View for access request (signup)
def access_request(request):
    if request.method == 'POST':
        form = AccessRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Prevent duplicate unapproved requests
            if AccessRequest.objects.filter(email=email, is_approved=False).exists():
                messages.warning(request, 'You’ve already submitted a request. Please wait for approval.')
                return redirect('thank_you')

            access_request = form.save()

            # Optional email to admin
            send_mail(
                'New DuxtHealth Access Request',
                f"""
                Full Name: {access_request.full_name}
                Email: {access_request.email}
                Profession: {access_request.profession}
                Message: {access_request.message}
                """,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )

            return redirect('thank_you')  # ✅ Redirect to thank you page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AccessRequestForm()

    return render(request, 'accounts/signup.html', {'form': form})


# Login view
def login_view(request):
    if request.user.is_authenticated:
        return redirect('homecare:home')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('homecare:home')

    return render(request, 'accounts/login.html', {'form': form})


# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')


# Admin-only: View access requests
@user_passes_test(lambda u: u.is_staff)
@login_required
def review_access_requests(request):
    requests = AccessRequest.objects.filter(is_approved=False)
    return render(request, 'accounts/pending_requests.html', {'requests': requests})


# Admin-only: Approve request and create user account
@user_passes_test(lambda u: u.is_staff)
@login_required


def approve_request(request, request_id):
    access_request = get_object_or_404(AccessRequest, id=request_id)

    # Generate a temporary password
    temp_password = get_random_string(length=8)

    # Create a user account
    user = User.objects.create_user(
        username=access_request.email,
        email=access_request.email,
        password=temp_password,
        first_name=access_request.full_name
    )

    access_request.is_approved = True
    access_request.save()

    # Send welcome email
    send_mail(
        'Your DuxtHealth Account Has Been Approved',
        f"""
        Dear {access_request.full_name},

        Your request to access DuxtHealth has been approved.

        You can now log in at: http://127.0.0.1:8000/accounts/login/

        Username: {access_request.email}
        Temporary Password: {temp_password}

        Please change your password after logging in: http://127.0.0.1:8000/accounts/change-password/

        Best,
        DuxtHealth Team
        """,
        settings.DEFAULT_FROM_EMAIL,
        [access_request.email],
        fail_silently=False,
    )

    messages.success(request, f"{access_request.full_name} approved and notified by email.")
    return redirect('review_access_requests')



# Thank you page after signup
def thank_you(request):
    return render(request, 'accounts/thank_you.html')

@login_required
def request_status_view(request):
    try:
        req = AccessRequest.objects.get(email=request.user.email)
        return render(request, 'accounts/request_status.html', {'request_obj': req})
    except AccessRequest.DoesNotExist:
        messages.info(request, "You haven't submitted a request.")
        return redirect('home')

