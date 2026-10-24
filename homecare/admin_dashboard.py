from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.db.models import Avg, Count

from homecare.models import (
    Patient,
    HealthProfessional,
    PatientFeedback
)


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        raise PermissionDenied("Admins only")

    # =========================
    # CORE METRICS
    # =========================
    total_patients = Patient.objects.count()
    total_staff = HealthProfessional.objects.count()
    total_feedback = PatientFeedback.objects.count()

    avg_rating = PatientFeedback.objects.aggregate(
        avg=Avg("overall_rating")
    )["avg"]

    # =========================
    # STAFF OVERVIEW
    # =========================
    # Recent staff (last 5 added, active or inactive)
    recent_staff = HealthProfessional.objects.all().order_by("-id")[:5]

    # Active and flagged staff counts
    active_staff_count = HealthProfessional.objects.filter(is_active=True).count()
    flagged_staff_count = HealthProfessional.objects.filter(is_flagged=True).count()

    # =========================
    # CRITICAL FEEDBACK
    # =========================
    low_feedbacks = PatientFeedback.objects.filter(
        overall_rating__lte=2
    ).select_related("patient").order_by("-id")[:5]

    # =========================
    # CONTEXT FOR TEMPLATE
    # =========================
    context = {
        "total_patients": total_patients,
        "total_staff": total_staff,
        "total_feedback": total_feedback,
        "avg_rating": round(avg_rating, 1) if avg_rating else None,
        "recent_staff": recent_staff,
        "active_staff_count": active_staff_count,
        "flagged_staff_count": flagged_staff_count,
        "low_feedbacks": low_feedbacks,
    }

    return render(
        request,
        "homecare/admin/dashboard.html",
        context
    )
