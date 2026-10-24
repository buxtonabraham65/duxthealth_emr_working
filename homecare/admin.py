from django.contrib import admin
from .models import (
    Patient,
    HealthProfessional,
    PatientAssignment,
    CarePlan,
    VisitSchedule,
    VitalSignRecord,
    NursesNote,
    DoctorNote,
    NoteAddendum,
    MedicationSheet,
    MedicationSchedule,
    MedicationAdministration, 
    MedicationReaction,
    HomecareRequest,
    TreatmentSheet,
    HomecareApplication,
    PatientFeedback,
    DiagnosisRecord,
    EmergencyContact,
    Allergy,
    AIConversation,
    LabResult,
)

# ======================================================
# INLINE DEFINITIONS (SHOW UNDER PATIENT)
# ======================================================

class PatientAssignmentInline(admin.TabularInline):
    model = PatientAssignment
    extra = 0


class CarePlanInline(admin.TabularInline):
    model = CarePlan
    extra = 0
    show_change_link = True


class VisitScheduleInline(admin.TabularInline):
    model = VisitSchedule
    extra = 0
    show_change_link = True


class VitalSignInline(admin.TabularInline):
    model = VitalSignRecord
    extra = 0
    readonly_fields = ("recorded_at",)
    ordering = ("-recorded_at",)


class NursesNoteInline(admin.TabularInline):
    model = NursesNote
    extra = 0
    readonly_fields = ("created_at",)


class DoctorNoteInline(admin.TabularInline):
    model = DoctorNote
    extra = 0
    readonly_fields = ("created_at",)


class MedicationInline(admin.TabularInline):
    model = MedicationSheet
    extra = 0


# ======================================================
# PATIENT ADMIN (MAIN DASHBOARD)
# ======================================================

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "other_name",
        "gender",
        "date_of_birth",
        "contact_phone",
        "patient_code",
    )
    search_fields = (
        "first_name",
        "last_name",
        "other_name",
        "contact_phone",
        "patient_code",
    )
    list_filter = ("gender",)

    inlines = [
        PatientAssignmentInline,
        CarePlanInline,
        VisitScheduleInline,
        VitalSignInline,
        NursesNoteInline,
        DoctorNoteInline,
        MedicationInline,
    ]


# ======================================================
# HEALTH PROFESSIONALS
# ======================================================

@admin.register(HealthProfessional)
class HealthProfessionalAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "phone",
    )
    list_filter = ("role",)


# ======================================================
# PATIENT ASSIGNMENTS
# ======================================================

@admin.register(PatientAssignment)
class PatientAssignmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "professional", "assigned_at")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "other_name",
        "professional__user__username",
    )
    list_filter = ("assigned_at",)


# ======================================================
# CARE PLANS
# ======================================================

@admin.register(CarePlan)
class CarePlanAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "patient",
        "created_by",
        "start_date",
        "end_date",
        "is_active",
    )
    search_fields = (
        "title",
        "patient__first_name",
        "patient__last_name",
    )
    list_filter = ("is_active", "start_date", "end_date")


# ======================================================
# VISIT SCHEDULES
# ======================================================

@admin.register(VisitSchedule)
class VisitScheduleAdmin(admin.ModelAdmin):
    list_display = ("patient", "scheduled_date", "status")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
    )
    list_filter = ("status", "scheduled_date")


# ======================================================
# VITAL SIGNS
# ======================================================

@admin.register(VitalSignRecord)
class VitalSignRecordAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "recorded_by",
        "recorded_at",
        "temperature",
        "pulse",
        "respiratory_rate",
        "blood_pressure_systolic",
        "blood_pressure_diastolic",
        "oxygen_saturation",
    )
    search_fields = (
        "patient__first_name",
        "patient__last_name",
    )
    list_filter = ("recorded_at",)


# ======================================================
# NURSES NOTES
# ======================================================

@admin.register(NursesNote)
class NursesNoteAdmin(admin.ModelAdmin):
    list_display = ("patient", "created_by", "created_at")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
    )
    list_filter = ("created_at",)


# ======================================================
# DOCTOR NOTES
# ======================================================

@admin.register(DoctorNote)
class DoctorNoteAdmin(admin.ModelAdmin):
    list_display = ("patient", "created_by", "created_at")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
    )
    list_filter = ("created_at",)


# ======================================================
# NOTE ADDENDUMS
# ======================================================

@admin.register(NoteAddendum)
class NoteAddendumAdmin(admin.ModelAdmin):
    list_display = ("created_by", "created_at")
    search_fields = ("content",)
    list_filter = ("created_at",)

# ------------------------------------------------------
#Treatmentsheet

@admin.register(TreatmentSheet)
class TreatmentSheetAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "care_plan",
        "visit",
        "created_by",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("patient__full_name",)
# ------------------------------------------------------
# ======================================================
# MEDICATIONS
# ======================================================

@admin.register(MedicationSheet)
class MedicationSheetAdmin(admin.ModelAdmin):
    list_display = (
        "medication_name",
        "patient",
        "dosage",
        "frequency",
        "start_date",
        "end_date",
    )
    search_fields = (
        "medication_name",
        "patient__first_name",
        "patient__last_name",
    )
    list_filter = ("start_date", "end_date")


# ======================================================
# HOMECARE REQUESTS (PRE-PATIENT)
# ======================================================

@admin.register(HomecareRequest)
class HomecareRequestAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone",
        "service_type",
        "assigned_to",
        "is_contacted",
        "created_at",
    )
    list_filter = ("service_type", "is_contacted", "created_at")
    search_fields = ("full_name", "phone", "email")
    list_editable = ("assigned_to", "is_contacted")

#Patient feedback and rating of stafs and system
@admin.register(PatientFeedback)
class PatientFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "provider",
        "overall_rating",
        "flagged",
        "created_at",
    )
    list_filter = ("overall_rating", "flagged", "created_at")
    search_fields = ("patient__first_name", "comments")
    ordering = ("-created_at",)

#Diagnosis and diagnosis sumarry

@admin.register(DiagnosisRecord)
class DiagnosisRecordAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('patient', 'diagnosis', 'created_by', 'created_at')
    
    # Filter options on the right sidebar
    list_filter = ('created_at', 'created_by', 'patient')
    
    # Enable search for diagnosis text and patient/user names
    # Note: Assumes Patient and User models have a 'name' or 'username' field
    search_fields = ('diagnosis', 'summary', 'patient__name', 'created_by__username')
    
    # Make 'created_at' readable but not editable in the form
    readonly_fields = ('created_at',)
    
    # Organizing fields in the edit form
    fieldsets = (
        (None, {
            'fields': ('patient', 'diagnosis', 'summary')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',),  # Hidden by default
        }),
    )

    def save_model(self, request, obj, form, change):
        """Automatically set the created_by user to the current logged-in user."""
        if not obj.pk:  # Only set on initial creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(HomecareApplication)
class HomecareApplicationAdmin(admin.ModelAdmin):
    # ===============================
    # LIST VIEW (WHAT ADMIN SEES FIRST)
    # ===============================
    list_display = (
        "full_name",
        "phone_number",
        "location",
        "service_needed",
        "is_contacted",
        "created_at",
    )

    # ===============================
    # FILTERS (QUICK SORTING)
    # ===============================
    list_filter = (
        "is_contacted",
        "location",
        "service_needed",
        "created_at",
    )

    # ===============================
    # SEARCH (FAST LOOKUP)
    # ===============================
    search_fields = (
        "full_name",
        "phone_number",
        "whatsapp_number",
        "email",
        "location",
        "service_needed",
    )

    # ===============================
    # READABILITY & UX
    # ===============================
    ordering = ("-created_at",)
    list_per_page = 25
    date_hierarchy = "created_at"

    # ===============================
    # FIELD GROUPING (DETAIL PAGE)
    # ===============================
    fieldsets = (
        ("Applicant Information", {
            "fields": (
                "full_name",
                "phone_number",
                "whatsapp_number",
                "email",
            )
        }),
        ("Service Details", {
            "fields": (
                "service_needed",
                "location",
                "message",
            )
        }),
        ("Status", {
            "fields": (
                "is_contacted",
                "created_at",
            )
        }),
    )

    readonly_fields = ("created_at",)

    # ===============================
    # QUICK ACTIONS
    # ===============================
    actions = ["mark_as_contacted"]

    def mark_as_contacted(self, request, queryset):
        queryset.update(is_contacted=True)
        self.message_user(
            request,
            f"{queryset.count()} application(s) marked as contacted."
        )

    mark_as_contacted.short_description = "✅ Mark selected applications as contacted"


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "relationship",
        "phone_number",
        "patient",
    )

    search_fields = (
        "name",
        "relationship",
        "phone_number",
        "patient__first_name",
        "patient__last_name",
        "patient__patient_id",
    )

    list_filter = (
        "relationship",
    )

    ordering = ("name",)


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "allergy_type",
        "substance",
        "severity",
        "recorded_at",
    )

    search_fields = (
        "substance",
        "reaction",
        "patient__first_name",
        "patient__last_name",
        "patient__patient_id",
    )

    list_filter = (
        "allergy_type",
        "severity",
        "recorded_at",
    )

    date_hierarchy = "recorded_at"

    ordering = ("-recorded_at",)

#AI CONVERSATION

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'patient',
        'user',
        'short_user_message',
        'short_ai_response',
        'ip_address',
        'timestamp',
    )

    list_filter = (
        'timestamp',
        'patient',
    )

    search_fields = (
        'patient__first_name',
        'patient__last_name',
        'user__username',
        'user_message',
        'ai_response',
    )

    readonly_fields = (
        'timestamp',
        'ip_address',
    )

    ordering = ('-timestamp',)

    fieldsets = (
        ('Patient & User', {
            'fields': ('patient', 'user')
        }),
        ('Conversation', {
            'fields': ('user_message', 'ai_response')
        }),
        ('System Info', {
            'fields': ('ip_address', 'timestamp')
        }),
    )

    def short_user_message(self, obj):
        return obj.user_message[:50] + "..." if len(obj.user_message) > 50 else obj.user_message
    short_user_message.short_description = "User Message"

    def short_ai_response(self, obj):
        return obj.ai_response[:50] + "..." if len(obj.ai_response) > 50 else obj.ai_response
    short_ai_response.short_description = "AI Response"

#LAB
@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("patient", "title", "created_at")

# ==============================================================================
# INLINES
# Allows editing schedules and reactions inline inside relevant parent admins
# ==============================================================================

class MedicationScheduleInline(admin.TabularInline):
    model = MedicationSchedule
    extra = 1
    fields = ['scheduled_time', 'is_active', 'instructions', 'created_by']


class MedicationReactionInline(admin.StackedInline):
    model = MedicationReaction
    extra = 0
    fields = ['observed_at', 'severity', 'description', 'action_taken', 'clinician_notified']


# ==============================================================================
# MODEL ADMINS
# ==============================================================================

@admin.register(MedicationSchedule)
class MedicationScheduleAdmin(admin.ModelAdmin):
    list_display = ['get_medication_name', 'scheduled_time', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'scheduled_time', 'created_at']
    search_fields = ['medication__medication_name', 'instructions', 'created_by__user__username']
    ordering = ['scheduled_time']
    
    @admin.display(ordering='medication__medication_name', description='Medication')
    def get_medication_name(self, obj):
        return obj.medication.medication_name


@admin.register(MedicationAdministration)
class MedicationAdministrationAdmin(admin.ModelAdmin):
    list_display = ['get_medication_name', 'status', 'scheduled_for', 'administered_at', 'administered_by', 'recorded_at']
    list_filter = ['status', 'administered_at', 'route_used']
    search_fields = [
        'medication__medication_name', 
        'dose_given', 
        'route_used', 
        'administered_by__user__username', 
        'notes', 
        'reason_not_given'
    ]
    ordering = ['-recorded_at']
    inlines = [MedicationReactionInline]
    
    # Organize fields cleanly when editing an administration history entry
    fieldsets = (
        ('Core Details', {
            'fields': ('medication', 'schedule', 'status')
        }),
        ('Timing & Dosage', {
            'fields': ('scheduled_for', 'administered_at', 'dose_given', 'route_used')
        }),
        ('Staff & Notes', {
            'fields': ('administered_by', 'reason_not_given', 'notes')
        }),
    )

    @admin.display(ordering='medication__medication_name', description='Medication')
    def get_medication_name(self, obj):
        return obj.medication.medication_name


@admin.register(MedicationReaction)
class MedicationReactionAdmin(admin.ModelAdmin):
    list_display = ['get_medication_name', 'severity', 'observed_at', 'clinician_notified', 'recorded_by']
    list_filter = ['severity', 'clinician_notified', 'observed_at']
    search_fields = [
        'medication__medication_name', 
        'description', 
        'action_taken', 
        'follow_up_notes', 
        'recorded_by__user__username'
    ]
    ordering = ['-recorded_at']
    
    fieldsets = (
        ('Reaction Details', {
            'fields': ('medication', 'administration', 'severity', 'description', 'observed_at')
        }),
        ('Clinical Actions', {
            'fields': ('action_taken', 'clinician_notified', 'follow_up_notes')
        }),
        ('Audit Log', {
            'fields': ('recorded_by',),
        }),
    )

    @admin.display(ordering='medication__medication_name', description='Medication')
    def get_medication_name(self, obj):
        return obj.medication.medication_name

# ==============================================================================
# EXISTING MODEL ENHANCEMENT (Optional)
# If you want to view schedules right inside the MedicationSheet dashboard
# ==============================================================================
# admin.site.unregister(MedicationSheet) # Uncomment if already registered elsewhere
# @admin.register(MedicationSheet)
# class MedicationSheetAdmin(admin.ModelAdmin):
#     inlines = [MedicationScheduleInline]
