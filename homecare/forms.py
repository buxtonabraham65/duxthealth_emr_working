from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import (
    Patient, HealthProfessional, CarePlan, VisitSchedule,
    NursesNote, DoctorNote, TreatmentSheet, MedicationSheet, VitalSignRecord, HomecareRequest, HomecareApplication, 
)
from django.contrib.auth.models import User
from homecare.utils.access import get_visible_patients



class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'contact_phone', 'address']


class HealthProfessionalForm(forms.ModelForm):
    class Meta:
        model = HealthProfessional
        fields = ['role', 'phone']


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


from django import forms
from .models import CarePlan
from homecare.utils.access import get_visible_patients



class CarePlanForm(forms.ModelForm):
    # =========================
    # Embedded Diagnosis Fields
    # =========================
    diagnosis = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Primary diagnosis (e.g. Hypertension, Post-stroke recovery)'
        }),
        help_text="Enter the patient’s current diagnosis if applicable."
    )

    diagnosis_summary = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': (
                'Explain the patient’s condition, progress so far, '
                'improvements, reassurance, and care guidance in simple language.'
            )
        }),
        help_text="This summary will be visible to the patient."
    )

    class Meta:
        model = CarePlan
        fields = [
            'patient',
            'title',
            'problem',
            'objective',
            'intervention',
            'rational',
            'evaluation',
            'description',
            'start_date',
            'end_date',
            'is_active',
        ]

        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Care plan title'
            }),
            'problem': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Patient problem / nursing diagnosis'
            }),
            'objective': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Expected outcomes / goals'
            }),
            'intervention': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Planned nursing / medical interventions'
            }),
            'rational': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Clinical rationale for interventions'
            }),
            'evaluation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Evaluation after care delivery'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            self.fields['patient'].queryset = get_visible_patients(user)
        else:
            self.fields['patient'].queryset = self.fields['patient'].queryset.none()


class VisitScheduleForm(forms.ModelForm):
    class Meta:
        model = VisitSchedule
        fields = ['care_plan', 'scheduled_date', 'caregivers', 'status']
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'caregivers': forms.CheckboxSelectMultiple(),
        }


# ======================================================
# NURSES NOTE FORM
# ======================================================


class NursesNoteForm(forms.ModelForm):
    # Diagnosis entered or displayed alongside the nursing note
    diagnosis = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Enter patient diagnosis'
        })
    )

    # Diagnosis summary, progress, and advice
    diagnosis_summary = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter diagnosis summary / progress / advice'
        })
    )

    class Meta:
        model = NursesNote
        fields = [
            'patient',
            'note',
            'diagnosis',
            'diagnosis_summary',
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Restrict patient selection to patients visible to the current user.
        if user:
            self.fields['patient'].queryset = get_visible_patients(user)
        else:
            self.fields['patient'].queryset = (
                self.fields['patient'].queryset.none()
            )

        # When editing an existing nursing note, load the latest active
        # diagnosis record for that patient.
        if self.instance and self.instance.pk:
            patient = self.instance.patient

            if patient:
                diagnosis_record = (
                    DiagnosisRecord.objects
                    .filter(
                        patient=patient,
                        is_active=True
                    )
                    .order_by('-created_at', '-pk')
                    .first()
                )

                # A patient may not have an active diagnosis record.
                # In that case, leave both fields unchanged.
                if diagnosis_record:
                    self.fields['diagnosis'].initial = (
                        diagnosis_record.diagnosis or ''
                    )
                    self.fields['diagnosis_summary'].initial = (
                        diagnosis_record.summary or ''
                    )

# ======================================================
# DOCTOR NOTE FORM
# ======================================================

class DoctorNoteForm(forms.ModelForm):
    # Adding diagnosis fields
    diagnosis = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Patient diagnosis'
        })
    )
    diagnosis_summary = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Summary of patient progress, improvement, or care instructions'
        })
    )

    class Meta:
        model = DoctorNote
        fields = ['patient', 'note', 'diagnosis', 'diagnosis_summary']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter patient dropdown for the current user
        if user:
            self.fields['patient'].queryset = get_visible_patients(user)
        else:
            self.fields['patient'].queryset = self.fields['patient'].queryset.none()



# ======================================================
# TREATMENT SHEET FORM
# ======================================================

class TreatmentSheetForm(forms.ModelForm):
    class Meta:
        model = TreatmentSheet
        fields = ['patient', 'treatment_description']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            self.fields['patient'].queryset = get_visible_patients(user)
        else:
            self.fields['patient'].queryset = self.fields['patient'].queryset.none()


# ======================================================
# MEDICATION SHEET FORM
# ======================================================

class MedicationSheetForm(forms.ModelForm):
    class Meta:
        model = MedicationSheet
        fields = [
            'patient',
            'medication_name',
            'dosage',
            'frequency',
            'route',
            'start_date',
            'end_date',
            'notes'
        ]
        widgets = {
    'start_date': forms.DateInput(
        attrs={
            'type': 'date',
            'class': 'form-control',
            'style': 'max-width:220px;'
        }
    ),
    'end_date': forms.DateInput(
        attrs={
            'type': 'date',
            'class': 'form-control',
            'style': 'max-width:220px;'
        }
    ),
}


    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            self.fields['patient'].queryset = get_visible_patients(user)
        else:
            self.fields['patient'].queryset = self.fields['patient'].queryset.none()



# ======================================================
# MULTIPLE MEDICATIONS IN ONE SUBMISSION
# ======================================================

from django.forms import formset_factory


class MedicationOrderForm(forms.Form):
    """Shared patient information for a group of medicines."""

    patient = forms.ModelChoiceField(
        queryset=Patient.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    care_plan = forms.ModelChoiceField(
        queryset=CarePlan.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Related care plan (optional)"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            visible_patients = get_visible_patients(user)
            self.fields["patient"].queryset = visible_patients
            self.fields["care_plan"].queryset = CarePlan.objects.filter(
                patient__in=visible_patients
            )
        else:
            self.fields["patient"].queryset = Patient.objects.none()
            self.fields["care_plan"].queryset = CarePlan.objects.none()


class MedicationItemForm(forms.ModelForm):
    """One medication within a multi-medication submission."""

    class Meta:
        model = MedicationSheet
        fields = [
            "medication_name",
            "dosage",
            "frequency",
            "route",
            "start_date",
            "end_date",
            "notes",
        ]

        widgets = {
            "medication_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Medicine name"
            }),
            "dosage": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Prescribed dose"
            }),
            "frequency": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Prescribed frequency"
            }),
            "route": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Route of administration"
            }),
            "start_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "end_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Additional instructions"
            }),
        }


MedicationItemFormSet = formset_factory(
    MedicationItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class VitalSignRecordForm(forms.ModelForm):
    class Meta:
        model = VitalSignRecord
        fields = [
            'patient', 'care_plan', 'visit',
            'temperature', 'pulse', 'respiratory_rate',
            'blood_pressure_systolic', 'blood_pressure_diastolic',
            'oxygen_saturation',
            'blood_sugar_fbs', 'blood_sugar_rbs',
            'pain_score',
            'fluid_intake_oral', 'fluid_intake_iv', 'fluid_intake_tube',
            'fluid_output_urine', 'fluid_output_stool',
            'fluid_output_vomit', 'fluid_output_drains',
            'weight', 'height',
            'neuro_gcs_eye', 'neuro_gcs_verbal',
            'neuro_gcs_motor', 'neuro_avpu'
        ]
        widgets = {
            'temperature': forms.NumberInput(attrs={'step': '0.1'}),
            'oxygen_saturation': forms.NumberInput(attrs={'step': '0.1'}),
            'pain_score': forms.NumberInput(attrs={'min': 0, 'max': 10}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user:
            self.fields['patient'].queryset = get_visible_patients(user)
        else:
            # Safety fallback (no leakage)
            self.fields['patient'].queryset = Patient.objects.none()

    
        


# Homecare Request Form
class HomecareRequestForm(forms.ModelForm):
    class Meta:
        model = HomecareRequest
        fields = [
            "full_name",
            "phone",
            "email",
            "address",
            "service_type",
            "reason",
            "preferred_date",
        ]
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 4}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

#Register patient or homecare service forms

class HomecareApplicationForm(forms.ModelForm):
    class Meta:
        model = HomecareApplication
        fields = [
            "full_name",
            "phone_number",
            "whatsapp_number",
            "email",
            "location",
            "service_needed",
            "message",
        ]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }


# Diagnosis forms

from django import forms
from .models import DiagnosisRecord

class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = DiagnosisRecord
        fields = ["diagnosis", "summary"]
        widgets = {
            "diagnosis": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter diagnosis"
            }),
            "summary": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Diagnosis summary"
            }),
        }


# ======================================================
# ADDITIONAL DUxtHEALTH MEDICATION FORMS
# ======================================================

from .models import (
    MedicationSchedule,
    MedicationAdministration,
    MedicationReaction,
)


class MedicationScheduleForm(forms.ModelForm):
    class Meta:
        model = MedicationSchedule
        fields = ["scheduled_time", "instructions", "is_active"]
        widgets = {
            "scheduled_time": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "instructions": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional administration instructions",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class MedicationAdministrationForm(forms.ModelForm):
    class Meta:
        model = MedicationAdministration
        fields = [
            "schedule",
            "status",
            "scheduled_for",
            "administered_at",
            "dose_given",
            "route_used",
            "reason_not_given",
            "notes",
        ]
        widgets = {
            "schedule": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "scheduled_for": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "administered_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "dose_given": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "route_used": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "reason_not_given": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Required when a dose is withheld, refused, "
                        "missed, or otherwise not given."
                    ),
                }
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def __init__(self, *args, medication=None, **kwargs):
        super().__init__(*args, **kwargs)

        if medication is not None:
            self.fields["schedule"].queryset = (
                MedicationSchedule.objects.filter(
                    medication=medication,
                    is_active=True,
                )
            )
        else:
            self.fields["schedule"].queryset = (
                MedicationSchedule.objects.none()
            )

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        administered_at = cleaned.get("administered_at")
        dose_given = cleaned.get("dose_given")
        route_used = cleaned.get("route_used")
        reason = cleaned.get("reason_not_given")

        if status == "administered":
            if not administered_at:
                self.add_error(
                    "administered_at",
                    "Enter the actual date and time administered.",
                )
            if not dose_given:
                self.add_error(
                    "dose_given",
                    "Record the dose actually given.",
                )
            if not route_used:
                self.add_error(
                    "route_used",
                    "Record the route actually used.",
                )

        elif status in {"withheld", "refused", "not_given", "missed"}:
            if not reason:
                self.add_error(
                    "reason_not_given",
                    "Record the reason the dose was not given.",
                )

        return cleaned


class MedicationReactionForm(forms.ModelForm):
    class Meta:
        model = MedicationReaction
        fields = [
            "administration",
            "observed_at",
            "description",
            "severity",
            "action_taken",
            "clinician_notified",
            "follow_up_notes",
        ]
        widgets = {
            "administration": forms.Select(
                attrs={"class": "form-select"}
            ),
            "observed_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the observed or reported reaction",
                }
            ),
            "severity": forms.Select(
                attrs={"class": "form-select"}
            ),
            "action_taken": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "clinician_notified": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "follow_up_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def __init__(self, *args, medication=None, **kwargs):
        super().__init__(*args, **kwargs)

        if medication is not None:
            self.fields["administration"].queryset = (
                MedicationAdministration.objects.filter(
                    medication=medication
                )
            )
        else:
            self.fields["administration"].queryset = (
                MedicationAdministration.objects.none()
            )