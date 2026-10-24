from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta, date
from django.db import models

from homecare.models import *
from homecare.decorators import role_required


# ==============================
# VITAL ALERT ENGINE
# ==============================
def evaluate_vital(value, normal_min, normal_max, warn_margin=0):
    """
    Returns: status, color, message
    """
    if value is None:
        return "unknown", "secondary", "No data"

    if normal_min <= value <= normal_max:
        return "normal", "success", "Within normal range"

    if (normal_min - warn_margin) <= value <= (normal_max + warn_margin):
        return "warning", "warning", "Slightly outside normal range"

    return "critical", "danger", "Critical — needs attention"


@login_required
@role_required(['admin', 'patient'])
def dashboard(request):
    user = request.user

    # ==============================
    # PATIENT ACCESS
    # ==============================
    if hasattr(user, "patient_profile"):
        patient = user.patient_profile
        is_patient_view = True
    else:
        try:
            health_profile = user.healthprofessional
        except Exception:
            raise PermissionDenied("Access denied.")

        if health_profile.role != "admin":
            raise PermissionDenied("Access denied.")

        patient_id = request.GET.get("patient_id")
        if not patient_id:
            raise PermissionDenied("Patient not specified.")

        patient = get_object_or_404(Patient, id=patient_id)
        is_patient_view = False

    # ==============================
    # LAST 7 DAYS VITALS
    # ==============================
    seven_days_ago = timezone.now() - timedelta(days=7)

    vitals_7_days = VitalSignRecord.objects.filter(
        patient=patient,
        recorded_at__gte=seven_days_ago
    ).order_by("recorded_at")

    latest_vitals = vitals_7_days.last()

    # ==============================
    # CARE TEAM
    # ==============================
    assignments = PatientAssignment.objects.filter(patient=patient)
    doctors = assignments.filter(professional__role="doctor")
    nurses = assignments.filter(professional__role="nurse")

    # ==============================
    # UPCOMING VISIT
    # ==============================
    next_visit = VisitSchedule.objects.filter(
        patient=patient,
        scheduled_date__gte=timezone.now(),
        status="scheduled"
    ).order_by("scheduled_date").first()

    # ==============================
    # ACTIVE MEDICATIONS
    # ==============================
    today = date.today()

    medications = MedicationSheet.objects.filter(
        patient=patient,
        start_date__lte=today
    ).filter(
        models.Q(end_date__isnull=True) |
        models.Q(end_date__gte=today)
    ).order_by("medication_name")

    # ==============================
    # DIAGNOSIS (PATIENT VIEW LOGIC)
    # ==============================
    diagnosis_record = None

    latest_diagnosis = DiagnosisRecord.objects.filter(
        patient=patient
    ).order_by("-created_at").first()

    if latest_diagnosis:
        # Show only if within last 24 hours
        if timezone.now() - latest_diagnosis.created_at <= timedelta(hours=24):
            diagnosis_record = latest_diagnosis

    # ==============================
    # ALERT CALCULATIONS
    # ==============================
    alerts = {}

    if latest_vitals:
        alerts["bp_sys"] = evaluate_vital(
            latest_vitals.blood_pressure_systolic, 90, 120, warn_margin=20
        )
        alerts["bp_dia"] = evaluate_vital(
            latest_vitals.blood_pressure_diastolic, 60, 80, warn_margin=10
        )
        alerts["pulse"] = evaluate_vital(
            latest_vitals.pulse, 60, 100, warn_margin=15
        )
        alerts["temp"] = evaluate_vital(
            latest_vitals.temperature, 36.1, 37.2, warn_margin=0.7
        )
        alerts["resp"] = evaluate_vital(
            latest_vitals.respiratory_rate, 12, 20, warn_margin=4
        )
        alerts["oxygen"] = evaluate_vital(
            latest_vitals.oxygen_saturation, 95, 100, warn_margin=3
        )
        alerts["fbs"] = evaluate_vital(
            latest_vitals.blood_sugar_fbs, 4.0, 6.0, warn_margin=1.5
        )
        alerts["rbs"] = evaluate_vital(
            latest_vitals.blood_sugar_rbs, 4.0, 7.8, warn_margin=2.0
        )

    # ==============================
    # CONTEXT
    # ==============================
    context = {
        "patient": patient,
        "latest_vitals": latest_vitals,
        "vitals_7_days": vitals_7_days,
        "alerts": alerts,

        "care_team": {
            "doctors": doctors,
            "nurses": nurses,
            "next_visit": next_visit,
        },

        "medications": medications,

        # 👇 ONLY latest, auto-expiring diagnosis
        "diagnosis_record": diagnosis_record,

        "emergency_number": "+233551841350",
    }

    return render(request, "patient_dashboard/dashboard.html", context)
