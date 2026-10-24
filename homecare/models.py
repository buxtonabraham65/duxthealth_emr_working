from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import uuid
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


#======================================================
#PATIENT
#======================================================
class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
        null=True,
        blank=True,
        help_text="Login account for the patient. Must NOT be a staff account."
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_name = models.CharField(max_length=100, blank=True, null = True)
    date_of_birth = models.DateField()

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]

    contact_phone = models.CharField(max_length=20)
    address = models.TextField()
    nationality = models.CharField(max_length=100, default='Ghana')
    primary_language = models.CharField(max_length=100, blank=True, null = True)

    diagnosis = models.CharField(max_length=1000, null=True, blank=True)
    diagnosis_summary = models.TextField(null=True, blank=True)
    blood_group = models.CharField(max_length=20, blank=True, null = True)
    genotype = models.CharField(max_length=20, blank=True, null = True)
    medical_history = models.TextField(null = True, blank = True)
    

    patient_code = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    created_at = models.DateTimeField(default=timezone.now)

    # Admin control
    is_active = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)

    from datetime import date

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if hasattr(self, "date_of_birth") and self.date_of_birth:
            today = self.date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return "N/A"



    # 🔒 HARD VALIDATION
    def clean(self):
        if self.user and hasattr(self.user, "healthprofessional"):
            raise ValidationError(
                "This user already belongs to a Health Professional. "
                "A staff user cannot be a patient."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



# ======================================================
# HEALTH PROFESSIONALS
# ======================================================

class HealthProfessional(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('caregiver', 'Caregiver'),
        ('admin', 'Admin'),
        ('outreach_0fficer','Outreach_0fficer')
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    registration_number = models.CharField(max_length = 50, null = True, blank = True)
    pin = models.CharField(max_length = 50, null = True, blank = True)
    location = models.TextField(null =True, blank = True)
    address = models.TextField(null =True, blank = True)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"


# ======================================================
# PATIENT ASSIGNMENTS (ACCESS CONTROL)
# ======================================================

class PatientAssignment(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    professional = models.ForeignKey(
        HealthProfessional,
        on_delete=models.CASCADE,
        related_name="patient_assignments"
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("patient", "professional")

    def __str__(self):
        return f"{self.professional} → {self.patient}"


# ======================================================
# CARE PLANS
# ======================================================

from django.utils import timezone

class CarePlan(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='care_plans')
    created_by = models.ForeignKey(HealthProfessional, on_delete=models.SET_NULL, null=True, related_name='created_care_plans')

    title = models.CharField(max_length=200, null = True, blank = True)
    problem = models.TextField(null = True, blank= True)
    objective = models.TextField(null = True, blank = True)
    intervention = models.TextField(null = True, blank = True)
    rational = models.TextField(null = True, blank = True)
    evaluation = models.TextField(null = True, blank = True)

    # ✅ MUST BE NULLABLE (you already had existing rows)
    description = models.TextField(null=True, blank=True)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    STATUS_CHOICES = [
    ('ongoing', 'Ongoing'),
    ('achieved', 'Goals Achieved'),
    ('partially_achieved', 'Partially Achieved'),
    ('not_achieved', 'Goals Not Achieved'),
    ('discontinued', 'Discontinued'), 
    ]

    status = models.CharField(
    max_length=30,
    choices=STATUS_CHOICES,
    default='ongoing',
    db_index=True,)

    closed_at = models.DateTimeField(
    null=True,
    blank=True,
    )

    closure_notes = models.TextField(
    blank=True,
    default='',
    )

    # ✅ TEMP SAFE DEFAULT
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.patient}"




# ======================================================
# VISIT SCHEDULING
# ======================================================

class VisitSchedule(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="scheduled_visits"
    )
    care_plan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name='visits', null = True, blank = True)
    scheduled_date = models.DateTimeField()

    caregivers = models.ManyToManyField(
        HealthProfessional,
        related_name='scheduled_visits',
        blank=True
    )

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    def __str__(self):
        if self.care_plan:
            return f"Visit on {self.scheduled_date} for {self.care_plan.patient}"
            return f"Visit on {self.scheduled_date} for {self.patient}"



# ======================================================
# VITAL SIGNS
# ======================================================

class VitalSignRecord(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="vital_signs"
    )
    care_plan = models.ForeignKey(
        CarePlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vital_signs"
    )
    visit = models.ForeignKey(
        VisitSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vital_signs"
    )

    recorded_by = models.ForeignKey(
        HealthProfessional,
        on_delete=models.SET_NULL,
        null=True
    )

    recorded_at = models.DateTimeField(auto_now_add=True)

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(45)]
    )

    pulse = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(250)]
    )

    respiratory_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(5), MaxValueValidator(80)]
    )

    blood_pressure_systolic = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(300)]
    )

    blood_pressure_diastolic = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(200)]
    )

    oxygen_saturation = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(100)]
    )

    blood_sugar_fbs = models.DecimalField(
        max_digits=4,       # Allows numbers up to 999.9 (e.g., 585.5)
        decimal_places=1,   # Keeps 1 digit after the decimal point (e.g., 3.5)
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('0.0')), 
            MaxValueValidator(Decimal('600.0'))
        ]
    )

    blood_sugar_rbs = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('0.0')), 
            MaxValueValidator(Decimal('600.0'))
        ]
    )

    pain_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Pain level on a scale of 0 (no pain) to 10 (worst pain)"
    )

    fluid_intake_oral = models.PositiveIntegerField(null=True, blank=True)
    fluid_intake_iv = models.PositiveIntegerField(null=True, blank=True)
    fluid_intake_tube = models.PositiveIntegerField(null=True, blank=True)

    fluid_output_urine = models.PositiveIntegerField(null=True, blank=True)
    fluid_output_stool = models.PositiveIntegerField(null=True, blank=True)
    fluid_output_vomit = models.PositiveIntegerField(null=True, blank=True)
    fluid_output_drains = models.PositiveIntegerField(null=True, blank=True)

    weight = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )

    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30)]
    )

    # Glasgow Coma Scale
    neuro_gcs_eye = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Eye response (1-4)"
    )

    neuro_gcs_verbal = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Verbal response (1-5)"
    )

    neuro_gcs_motor = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        help_text="Motor response (1-6)"
    )

    neuro_avpu = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Level of consciousness: Alert, Verbal, Pain, Unresponsive"
    )

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"Vitals – {self.patient} ({self.recorded_at})"


# ======================================================
# CLINICAL NOTES (IMMUTABLE)
# ======================================================

class NursesNote(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="nurse_notes"
    )
    care_plan = models.ForeignKey(
        CarePlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    visit = models.ForeignKey(
        VisitSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        HealthProfessional,
        on_delete=models.SET_NULL,
        null=True
    )

    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nurse Note – {self.patient}"


class DoctorNote(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="doctor_notes"
    )
    care_plan = models.ForeignKey(
        CarePlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    visit = models.ForeignKey(
        VisitSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        HealthProfessional,
        on_delete=models.SET_NULL,
        null=True
    )

    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Doctor Note – {self.patient}"


# ======================================================
# NOTE ADDENDUMS
# ======================================================

class NoteAddendum(models.Model):
    doctor_note = models.ForeignKey(
        DoctorNote,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="addendums"
    )
    nurse_note = models.ForeignKey(
        NursesNote,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="addendums"
    )

    created_by = models.ForeignKey(
        HealthProfessional,
        on_delete=models.SET_NULL,
        null=True
    )

    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Addendum by {self.created_by}"


# ======================================================
# TREATMENTSHEET
# ======================================================

class TreatmentSheet(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="treatment_sheets"
    )
    care_plan = models.ForeignKey(
        CarePlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    visit = models.ForeignKey(
        VisitSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        HealthProfessional,
        on_delete=models.SET_NULL,
        null=True
    )

    treatment_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Treatment – {self.patient}"


# ======================================================
# MEDICATIONS
# ======================================================

class MedicationSheet(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="medications"
    )
    care_plan = models.ForeignKey(
        CarePlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    route = models.CharField(max_length=100)

    status = models.CharField(
    max_length=20,
    choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('discontinued', 'Discontinued'),
        ('on_hold', 'On Hold'),
    ],
    default='active',
    db_index=True,
)

    completed_at = models.DateTimeField(
    null=True,
    blank=True,
)

    completion_notes = models.TextField(blank=True)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(HealthProfessional,on_delete=models.SET_NULL,null=True)

    def __str__(self):
        return f"{self.medication_name} – {self.patient}"


# ======================================================
# DUxtHEALTH MEDICATION MANAGEMENT - ADDITIONAL MODELS
# Keep the existing MedicationSheet model unchanged.
# Add these classes directly below MedicationSheet.
# ======================================================

class MedicationSchedule(models.Model):
    """
    A scheduled administration time for an existing prescription.
    A medication may have multiple scheduled times.
    """

    medication = models.ForeignKey(
        MedicationSheet,
        on_delete=models.CASCADE,
        related_name="schedules"
    )

    scheduled_time = models.TimeField()

    is_active = models.BooleanField(default=True)

    instructions = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        HealthProfessional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_medication_schedules"
    )

    class Meta:
        ordering = ["scheduled_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["medication", "scheduled_time"],
                name="unique_medication_scheduled_time"
            )
        ]

    def __str__(self):
        return (
            f"{self.medication.medication_name} "
            f"at {self.scheduled_time}"
        )


class MedicationAdministration(models.Model):
    """
    Records what happened with one medication dose.
    This records administration history, not just the schedule.
    """

    STATUS_CHOICES = [
        ("administered", "Administered"),
        ("withheld", "Withheld"),
        ("refused", "Patient refused"),
        ("not_given", "Not given"),
        ("missed", "Missed"),
    ]

    medication = models.ForeignKey(
        MedicationSheet,
        on_delete=models.PROTECT,
        related_name="administration_records"
    )

    schedule = models.ForeignKey(
        MedicationSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="administration_records"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    scheduled_for = models.DateTimeField(
        null=True,
        blank=True
    )

    administered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    dose_given = models.CharField(
        max_length=100,
        blank=True
    )

    route_used = models.CharField(
        max_length=100,
        blank=True
    )

    administered_by = models.ForeignKey(
        HealthProfessional,
        on_delete=models.PROTECT,
        related_name="medication_administrations"
    )

    reason_not_given = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return (
            f"{self.medication.medication_name} - "
            f"{self.get_status_display()}"
        )


class MedicationReaction(models.Model):
    """
    Records an observed or reported reaction associated with
    a medication. A reaction may also be linked to an
    individual administration event.
    """

    SEVERITY_CHOICES = [
        ("unknown", "Not yet assessed"),
        ("mild", "Mild"),
        ("moderate", "Moderate"),
        ("severe", "Severe"),
    ]

    medication = models.ForeignKey(
        MedicationSheet,
        on_delete=models.PROTECT,
        related_name="reaction_records"
    )

    administration = models.ForeignKey(
        MedicationAdministration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reactions"
    )

    observed_at = models.DateTimeField()

    description = models.TextField()

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default="unknown"
    )

    action_taken = models.TextField(blank=True)

    clinician_notified = models.BooleanField(default=False)

    follow_up_notes = models.TextField(blank=True)

    recorded_by = models.ForeignKey(
        HealthProfessional,
        on_delete=models.PROTECT,
        related_name="recorded_medication_reactions"
    )

    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return (
            f"Reaction: {self.medication.medication_name} "
            f"({self.get_severity_display()})"
        )



# ======================================================
# HOMECARE REQUESTS (PRE-PATIENT)
# ======================================================

class HomecareRequest(models.Model):
    SERVICE_CHOICES = [
        ("nursing", "Nursing Care"),
        ("doctor", "Doctor Visit"),
        ("physio", "Physiotherapy"),
        ("lab", "Lab Sample Collection"),
        ("other", "Other"),
    ]

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()

    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    reason = models.TextField()

    preferred_date = models.DateField(null=True, blank=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_homecare_requests"
    )

    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} – {self.service_type}"

#homecare application
class HomecareApplication(models.Model):
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    whatsapp_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    location = models.CharField(max_length=255)
    service_needed = models.CharField(max_length=255)
    message = models.TextField(blank=True)

    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.service_needed}"


#Patient feedback and rating of staffs
class PatientFeedback(models.Model):
    RATING_CHOICES = [
        (1, "Very Poor"),
        (2, "Poor"),
        (3, "Average"),
        (4, "Good"),
        (5, "Excellent"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    provider = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="received_feedback"
    )
    visit = models.ForeignKey(
        "VisitSchedule", on_delete=models.SET_NULL, null=True, blank=True
    )

    overall_rating = models.IntegerField(choices=RATING_CHOICES)
    communication_rating = models.IntegerField(choices=RATING_CHOICES)
    professionalism_rating = models.IntegerField(choices=RATING_CHOICES)
    timeliness_rating = models.IntegerField(choices=RATING_CHOICES)

    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    flagged = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Auto-flag poor feedback
        if self.overall_rating <= 2:
            self.flagged = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Feedback by {self.patient} ({self.overall_rating}/5)"

#Diagnosis and diagnosis summary
# ======================================================
# DIAGNOSIS TIMELINE / HISTORY
# ======================================================

class DiagnosisRecord(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="diagnosis_records"
    )

    diagnosis = models.CharField(max_length=1000)
    summary = models.TextField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.patient} - {self.created_at.date()}"

#EMERGENCY CONTACTS
class EmergencyContact(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='emergency_contacts'
    )
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.relationship})"


#ALLERGIES

class Allergy(models.Model):
    ALLERGY_TYPE_CHOICES = [
        ('drug', 'Drug'),
        ('food', 'Food'),
        ('environment', 'Environment'),
        ('none','No known allergy'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='allergies'
    )
    allergy_type = models.CharField(max_length=20, choices=ALLERGY_TYPE_CHOICES)
    substance = models.CharField(max_length=400, blank = True, null = True)
    reaction = models.TextField(blank=True, null = True)
    severity = models.CharField(max_length=50, blank=True, null = True)

    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.substance} ({self.patient})"

#AI conversation
from django.db import models
from django.contrib.auth.models import User


class AIConversation(models.Model):
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name="ai_conversations"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    user_message = models.TextField()
    ai_response = models.TextField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"AI Chat - {self.patient} - {self.timestamp}"

class LabResult(models.Model):
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE, related_name="lab_results")
    title = models.CharField(max_length=255)
    result_text = models.TextField(blank=True, null=True)
    result_image = models.ImageField(upload_to="lab_results/", blank=True, null=True)
    extracted_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.patient}"

        