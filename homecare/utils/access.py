from homecare.models import Patient


def get_staff_profile(user):
    if not hasattr(user, "healthprofessional"):
        return None
    return user.healthprofessional


def get_visible_patients(user):
    """
    Returns ONLY ACTIVE patients visible to the current user.
    Discharged (is_active=False) patients are automatically excluded.
    """

    # 🔒 Safety: no anonymous access
    if not user or not user.is_authenticated:
        return Patient.objects.none()

    # 🔒 Must be a health professional
    if not hasattr(user, "healthprofessional"):
        return Patient.objects.none()

    hp = user.healthprofessional

    # ✅ BASE QUERYSET — ONLY ACTIVE PATIENTS
    base_queryset = Patient.objects.filter(is_active=True)

    # 👑 Admin sees all ACTIVE patients
    if hp.role == "admin":
        return base_queryset

    # 👩🏽‍⚕️ Doctor / Nurse / Caregiver see ACTIVE patients assigned to them
    if hp.role in ["doctor", "nurse", "caregiver"]:
        return base_queryset.filter(
            assignments__professional=hp
        ).distinct()

    # 🔒 Default fallback (no data leakage)
    return Patient.objects.none()