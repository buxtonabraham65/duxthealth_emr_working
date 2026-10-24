from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                raise PermissionDenied("You must be logged in to access this page.")

            # ===============================
            # PATIENT ACCESS SUPPORT (ADDED)
            # ===============================
            if "patient" in allowed_roles:
                # If user is a patient (has Patient profile)
                if hasattr(user, "patient_profile"):
                    return view_func(request, *args, **kwargs)

            # ===============================
            # HEALTH PROFESSIONAL ACCESS (UNCHANGED LOGIC)
            # ===============================
            try:
                profile = user.healthprofessional
            except Exception:
                raise PermissionDenied("You do not have permission to access this page.")

            if profile.role not in allowed_roles:
                raise PermissionDenied("You do not have permission to access this page.")

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
