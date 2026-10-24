from django.urls import path
from .views import dashboard

app_name = "patient_dashboard"

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
]
