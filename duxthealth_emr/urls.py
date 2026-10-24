from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls import handler403

handler403 = "duxthealth_emr.views.custom_403"


urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication views
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Include app routes
    path('records/', include('records.urls')),

    # Include accounts app for sign-up / access request
    path('accounts/', include('accounts.urls')),  # 👈 Add this line

    #Homecare homepage
    path('', include('homecare.urls')),


    path("patient/", include("patient_dashboard.urls")),






]


