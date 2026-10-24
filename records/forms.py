from django import forms
from .models import Patient, VitalSign, Consultation, Note, Outreach


class PatientForm(forms.ModelForm):
    outreach = forms.ModelChoiceField(
        queryset=Outreach.objects.all(),
        required=False,
        label="Outreach Event"
    )

    class Meta:
        model = Patient
        fields = [
            'full_name',
            'dob',
            'gender',
            'phone',
            'community',
            'allergies',
            'medical_history',
            'outreach'
        ]


class VitalSignForm(forms.ModelForm):
    outreach = forms.ModelChoiceField(
        queryset=Outreach.objects.all(),
        required=False,
        label="Vital Signs"
    )

    class Meta:
        model = VitalSign
        exclude = ['recorded_by', 'date_recorded', 'bmi']


class ConsultationForm(forms.ModelForm):
    outreach = forms.ModelChoiceField(
        queryset=Outreach.objects.all(),
        required=False,
        label="Outreach Event"
    )

    class Meta:
        model = Consultation
        exclude = ['created_by', 'created_at']


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        exclude = ['created_by', 'created_at']
