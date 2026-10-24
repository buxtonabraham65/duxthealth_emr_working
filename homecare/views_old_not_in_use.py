from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.db.models import Avg
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from .models import (Patient, HealthProfessional, CarePlan, VisitSchedule,NursesNote, DoctorNote, TreatmentSheet, MedicationSheet, VitalSignRecord, PatientFeedback)
from django.views.decorators.http import require_POST
from homecare.decorators import role_required
from .forms import (PatientForm, HealthProfessionalForm, UserForm, CarePlanForm, VisitScheduleForm,NursesNoteForm, DoctorNoteForm, TreatmentSheetForm, MedicationSheetForm, VitalSignRecordForm, HomecareApplicationForm)
from homecare.models import (Patient,HealthProfessional,PatientFeedback,DiagnosisRecord)
from DuxtHealth_AI.ai_modules.clinical_copilot import ClinicalAICopilot



# -------------------------------
# Homecare Home
# -------------------------------
@login_required
@role_required(['admin', 'doctor', 'nurse'])
def homecare_home(request):
    return render(request, 'homecare/homecare.html')

# -------------------------------
# Patient CRUD
# -------------------------------
@login_required
@role_required(['admin', 'doctor', 'nurse'])
def patient_list(request):
    hp = getattr(request.user, 'healthprofessional', None)

    if not hp:
        return HttpResponseForbidden("No health professional profile")

    if hp.role in ['doctor', 'nurse']:
        patients = Patient.objects.filter(
            assignments__professional=hp
        ).distinct()
    elif hp.role == 'admin':
        patients = Patient.objects.filter(is_active=True).order_by("-created_at")
    else:
        return HttpResponseForbidden("Unauthorized role")

    return render(request, 'homecare/patient_list.html', {'patients': patients})

@login_required
@role_required(['admin', 'doctor'])
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homecare:patient_list')
    else:
        form = PatientForm()
    return render(request, 'homecare/patient_form.html', {'form': form})

@login_required
@role_required(['admin', 'doctor'])
def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('homecare:patient_list')
    else:
        form = PatientForm(instance=patient)
    return render(request, 'homecare/patient_form.html', {'form': form})

@login_required
@role_required(['admin'])
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient.delete()
        return redirect('homecare:patient_list')
    return render(request, 'homecare/patient_confirm_delete.html', {'patient': patient})

# -------------------------------
# Health Professional CRUD
# -------------------------------
@login_required
@role_required(['admin'])
def professional_list(request):
    professionals = HealthProfessional.objects.all()
    return render(request, 'homecare/professional_list.html', {'professionals': professionals})

@login_required
@role_required(['admin'])
def professional_create(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        prof_form = HealthProfessionalForm(request.POST)
        if user_form.is_valid() and prof_form.is_valid():
            user = user_form.save()
            prof = prof_form.save(commit=False)
            prof.user = user
            prof.save()
            return redirect('homecare:professional_list')
    else:
        user_form = UserForm()
        prof_form = HealthProfessionalForm()
    return render(request, 'homecare/professional_form.html', {'user_form': user_form, 'prof_form': prof_form})

@login_required
@role_required(['admin'])
def professional_update(request, pk):
    prof = get_object_or_404(HealthProfessional, pk=pk)
    user = prof.user
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        prof_form = HealthProfessionalForm(request.POST, instance=prof)
        if user_form.is_valid() and prof_form.is_valid():
            user_form.save()
            prof_form.save()
            return redirect('homecare:professional_list')
    else:
        user_form = UserForm(instance=user)
        prof_form = HealthProfessionalForm(instance=prof)
    return render(request, 'homecare/professional_form.html', {'user_form': user_form, 'prof_form': prof_form})

@login_required
@role_required(['admin'])
def professional_delete(request, pk):
    prof = get_object_or_404(HealthProfessional, pk=pk)
    if request.method == 'POST':
        prof.user.delete()
        return redirect('homecare:professional_list')
    return render(request, 'homecare/professional_confirm_delete.html', {'professional': prof})

# -------------------------------
# CarePlan CRUD
# -------------------------------
# =============================
# CARE PLAN LIST
# =============================


# =============================
# CARE PLAN CREATE
# =============================
@login_required
@role_required(['admin', 'doctor'])
def careplan_create(request):
    # MUST have a patient to create a care plan
    patient_id = request.GET.get("patient")
    if not patient_id:
        raise PermissionDenied("Patient must be selected to create a care plan.")

    patient = get_object_or_404(Patient, pk=patient_id)

    if request.method == 'POST':
        form = CarePlanForm(request.POST)
        if form.is_valid():
            careplan = form.save(commit=False)
            careplan.patient = patient
            careplan.created_by = getattr(request.user, 'healthprofessional', None)
            careplan.save()
            return redirect('homecare:careplan_list')
    else:
        # Pre-fill patient in the form
        form = CarePlanForm(initial={"patient": patient})

    return render(request, 'homecare/careplan_form.html', {
        'form': form,
        'patient': patient
    })

# =============================
# CARE PLAN UPDATE
# =============================
@login_required
@role_required(['admin', 'doctor'])
def careplan_update(request, pk):
    careplan = get_object_or_404(CarePlan, pk=pk)

    # LOCKED care plans cannot be edited
    if getattr(careplan, 'signoff', None):
        raise PermissionDenied("This care plan has been signed and is now locked.")

    if request.method == 'POST':
        form = CarePlanForm(request.POST, instance=careplan)
        if form.is_valid():
            form.save()
            return redirect('homecare:careplan_list')
    else:
        form = CarePlanForm(instance=careplan)

    return render(request, 'homecare/careplan_form.html', {
        'form': form,
        'careplan': careplan,
        'patient': careplan.patient
    })

# =============================
# CARE PLAN DELETE
# =============================
@login_required
@role_required(['admin'])
def careplan_delete(request, pk):
    careplan = get_object_or_404(CarePlan, pk=pk)

    if request.method == 'POST':
        careplan.delete()
        return redirect('homecare:careplan_list')

    return render(request, 'homecare/careplan_confirm_delete.html', {'careplan': careplan})

# -------------------------------
# VisitSchedule CRUD
# -------------------------------


@login_required
@role_required(['admin', 'doctor'])
def visitschedule_create(request):
    if request.method == 'POST':
        form = VisitScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homecare:visitschedule_list')
    else:
        form = VisitScheduleForm()
    return render(request, 'homecare/visitschedule_form.html', {'form': form})

@login_required
@role_required(['admin', 'doctor'])
def visitschedule_update(request, pk):
    visit = get_object_or_404(VisitSchedule, pk=pk)
    if request.method == 'POST':
        form = VisitScheduleForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect('homecare:visitschedule_list')
    else:
        form = VisitScheduleForm(instance=visit)
    return render(request, 'homecare/visitschedule_form.html', {'form': form})

@login_required
@role_required(['admin'])
def visitschedule_delete(request, pk):
    visit = get_object_or_404(VisitSchedule, pk=pk)
    if request.method == 'POST':
        visit.delete()
        return redirect('homecare:visitschedule_list')
    return render(request, 'homecare/visitschedule_confirm_delete.html', {'visit': visit})

# -------------------------------
# NursesNote CRUD
# -------------------------------

@login_required
@role_required(['admin', 'nurse'])
def nursesnote_create(request):
    if request.method == 'POST':
        form = NursesNoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homecare:nursesnote_list')
    else:
        form = NursesNoteForm()
    return render(request, 'homecare/nursesnote_form.html', {'form': form})

@login_required
@role_required(['admin', 'nurse'])
def nursesnote_update(request, pk):
    note = get_object_or_404(NursesNote, pk=pk)
    if request.method == 'POST':
        form = NursesNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('homecare:nursesnote_list')
    else:
        form = NursesNoteForm(instance=note)
    return render(request, 'homecare/nursesnote_form.html', {'form': form})

@login_required
@role_required(['admin'])
def nursesnote_delete(request, pk):
    note = get_object_or_404(NursesNote, pk=pk)
    if request.method == 'POST':
        note.delete()
        return redirect('homecare:nursesnote_list')
    return render(request, 'homecare/nursesnote_confirm_delete.html', {'note': note})

# -------------------------------
# DoctorNote CRUD
# -------------------------------
@login_required
@role_required(['admin', 'doctor'])
def doctornote_list(request):
    notes = DoctorNote.objects.all()
    return render(request, 'homecare/doctornote_list.html', {'notes': notes})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from homecare.decorators import role_required
from .models import DoctorNote
from .forms import DoctorNoteForm


# ======================================================
# CREATE DOCTOR NOTE
# ======================================================

@login_required
@role_required(['admin', 'doctor'])
def doctornote_create(request):
    if request.method == 'POST':
        form = DoctorNoteForm(request.POST, user=request.user)
        if form.is_valid():
            # Save DoctorNote
            note = form.save(commit=False)
            note.created_by = request.user.healthprofessional
            note.save()

            # Save diagnosis if provided
            diagnosis_text = form.cleaned_data.get('diagnosis')
            diagnosis_summary_text = form.cleaned_data.get('diagnosis_summary')

            if diagnosis_text or diagnosis_summary_text:
                # Create a new DiagnosisRecord linked to this patient
                from .models import DiagnosisRecord  # Ensure import at top if not already
                DiagnosisRecord.objects.create(
                    patient=note.patient,
                    diagnosis=diagnosis_text or "",
                    summary=diagnosis_summary_text or "",
                    created_by=request.user
                )

            return redirect('homecare:doctornote_list')
    else:
        form = DoctorNoteForm(user=request.user)

    return render(request, 'homecare/doctornote_form.html', {
        'form': form
    })



# ======================================================
# UPDATE DOCTOR NOTE
# ======================================================

@login_required
@role_required(['admin', 'doctor'])
def doctornote_update(request, pk):
    # Get the existing doctor note
    note = get_object_or_404(DoctorNote, pk=pk)

    if request.method == 'POST':
        form = DoctorNoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            updated_note = form.save()

            # Handle DiagnosisRecord
            diagnosis_text = form.cleaned_data.get('diagnosis')
            diagnosis_summary_text = form.cleaned_data.get('diagnosis_summary')

            if diagnosis_text or diagnosis_summary_text:
                from .models import DiagnosisRecord

                # Check if a DiagnosisRecord already exists for this patient
                diagnosis_record = DiagnosisRecord.objects.filter(patient=updated_note.patient).last()

                if diagnosis_record:
                    # Update existing record
                    diagnosis_record.diagnosis = diagnosis_text or diagnosis_record.diagnosis
                    diagnosis_record.summary = diagnosis_summary_text or diagnosis_record.summary
                    diagnosis_record.created_by = request.user
                    diagnosis_record.save()
                else:
                    # Create new record
                    DiagnosisRecord.objects.create(
                        patient=updated_note.patient,
                        diagnosis=diagnosis_text or "",
                        summary=diagnosis_summary_text or "",
                        created_by=request.user
                    )

            return redirect('homecare:doctornote_list')
    else:
        form = DoctorNoteForm(instance=note, user=request.user)

    return render(request, 'homecare/doctornote_form.html', {
        'form': form
    })



@login_required
@role_required(['admin'])
def doctornote_delete(request, pk):
    note = get_object_or_404(DoctorNote, pk=pk)
    if request.method == 'POST':
        note.delete()
        return redirect('homecare:doctornote_list')
    return render(request, 'homecare/doctornote_confirm_delete.html', {'note': note})

# -------------------------------
# TreatmentSheet CRUD
# -------------------------------
@login_required
@role_required(['admin', 'nurse'])
def treatmentsheet_list(request):
    sheets = TreatmentSheet.objects.all()
    return render(request, 'homecare/treatmentsheet_list.html', {'sheets': sheets})


# ======================================================
# CREATE TREATMENT SHEET
# ======================================================

@login_required
@role_required(['admin', 'nurse'])
def treatmentsheet_create(request):
    if request.method == 'POST':
        form = TreatmentSheetForm(request.POST, user=request.user)
        if form.is_valid():
            sheet = form.save(commit=False)
            sheet.created_by = request.user.healthprofessional
            sheet.save()
            return redirect('homecare:treatmentsheet_list')
    else:
        form = TreatmentSheetForm(user=request.user)

    return render(request, 'homecare/treatmentsheet_form.html', {
        'form': form
    })


# ======================================================
# UPDATE TREATMENT SHEET
# ======================================================

@login_required
@role_required(['admin', 'nurse'])
def treatmentsheet_update(request, pk):
    sheet = get_object_or_404(TreatmentSheet, pk=pk)

    if request.method == 'POST':
        form = TreatmentSheetForm(request.POST, instance=sheet, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('homecare:treatmentsheet_list')
    else:
        form = TreatmentSheetForm(instance=sheet, user=request.user)

    return render(request, 'homecare/treatmentsheet_form.html', {
        'form': form
    })


@login_required
@role_required(['admin'])
def treatmentsheet_delete(request, pk):
    sheet = get_object_or_404(TreatmentSheet, pk=pk)
    if request.method == 'POST':
        sheet.delete()
        return redirect('homecare:treatmentsheet_list')
    return render(request, 'homecare/treatmentsheet_confirm_delete.html', {'sheet': sheet})


# -------------------------------
# Patient CRUD
# -------------------------------


@login_required
@role_required(['admin'])
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homecare:patient_list')
    else:
        form = PatientForm()
    return render(request, 'homecare/patient_form.html', {'form': form})

@login_required
@role_required(['admin', 'doctor'])
def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('homecare:patient_list')
    else:
        form = PatientForm(instance=patient)
    return render(request, 'homecare/patient_form.html', {'form': form})

@login_required
@role_required(['admin'])
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient.delete()
        return redirect('homecare:patient_list')
    return render(request, 'homecare/patient_confirm_delete.html', {'patient': patient})

# -------------------------------
# Health Professional CRUD
# -------------------------------
@login_required
@role_required(['admin'])
def professional_list(request):
    professionals = HealthProfessional.objects.all()
    return render(request, 'homecare/professional_list.html', {'professionals': professionals})

@login_required
@role_required(['admin'])
def professional_create(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        prof_form = HealthProfessionalForm(request.POST)
        if user_form.is_valid() and prof_form.is_valid():
            user = user_form.save()
            prof = prof_form.save(commit=False)
            prof.user = user
            prof.save()
            return redirect('homecare:professional_list')
    else:
        user_form = UserForm()
        prof_form = HealthProfessionalForm()
    return render(request, 'homecare/professional_form.html', {'user_form': user_form, 'prof_form': prof_form})

@login_required
@role_required(['admin'])
def professional_update(request, pk):
    prof = get_object_or_404(HealthProfessional, pk=pk)
    user = prof.user
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        prof_form = HealthProfessionalForm(request.POST, instance=prof)
        if user_form.is_valid() and prof_form.is_valid():
            user_form.save()
            prof_form.save()
            return redirect('homecare:professional_list')
    else:
        user_form = UserForm(instance=user)
        prof_form = HealthProfessionalForm(instance=prof)
    return render(request, 'homecare/professional_form.html', {'user_form': user_form, 'prof_form': prof_form})

@login_required
@role_required(['admin'])
def professional_delete(request, pk):
    prof = get_object_or_404(HealthProfessional, pk=pk)
    if request.method == 'POST':
        prof.user.delete()
        return redirect('homecare:professional_list')
    return render(request, 'homecare/professional_confirm_delete.html', {'professional': prof})

# -------------------------------
# CarePlan CRUD
# -------------------------------
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

from homecare.decorators import role_required
from homecare.models import Patient, CarePlan, HealthProfessional
from homecare.forms import CarePlanForm


# ================================
# CARE PLAN LIST
# ================================

# ================================
# CARE PLAN CREATE
# ================================
@login_required
@role_required(['admin', 'doctor'])
def careplan_create(request):
    patient_id = request.GET.get("patient")
    if not patient_id:
        raise PermissionDenied("Patient must be selected to create a care plan.")

    patient = get_object_or_404(Patient, pk=patient_id)

    if request.method == 'POST':
        form = CarePlanForm(request.POST)
        if form.is_valid():
            careplan = form.save(commit=False)
            careplan.patient = patient
            careplan.created_by = getattr(request.user, 'healthprofessional', None)
            careplan.save()

            # ===== Update patient diagnosis fields =====
            patient.diagnosis = request.POST.get("diagnosis", patient.diagnosis)
            patient.diagnosis_summary = request.POST.get("diagnosis_summary", patient.diagnosis_summary)
            patient.save()

            return redirect('homecare:careplan_list')
    else:
        form = CarePlanForm(initial={"patient": patient})

    return render(request, 'homecare/careplan_form.html', {
        'form': form,
        'patient': patient
    })


# ================================
# CARE PLAN UPDATE
# ================================
@login_required
@role_required(['admin', 'doctor'])
def careplan_update(request, pk):
    careplan = get_object_or_404(CarePlan, pk=pk)
    patient = careplan.patient

    # Lock if signed off
    if getattr(careplan, 'signoff', None):
        raise PermissionDenied("This care plan has been signed and is now locked.")

    if request.method == 'POST':
        form = CarePlanForm(request.POST, instance=careplan)
        if form.is_valid():
            form.save()

            # ===== Update patient diagnosis fields =====
            patient.diagnosis = request.POST.get("diagnosis", patient.diagnosis)
            patient.diagnosis_summary = request.POST.get("diagnosis_summary", patient.diagnosis_summary)
            patient.save()

            return redirect('homecare:careplan_list')
    else:
        form = CarePlanForm(instance=careplan)

    return render(request, 'homecare/careplan_form.html', {
        'form': form,
        'careplan': careplan,
        'patient': patient
    })


# ================================
# CARE PLAN DELETE
# ================================
@login_required
@role_required(['admin'])
def careplan_delete(request, pk):
    careplan = get_object_or_404(CarePlan, pk=pk)
    if request.method == 'POST':
        careplan.delete()
        return redirect('homecare:careplan_list')
    return render(request, 'homecare/careplan_confirm_delete.html', {'careplan': careplan})

# -------------------------------

@login_required
@role_required(['admin', 'doctor'])
def visitschedule_create(request):
    if request.method == 'POST':
        form = VisitScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homecare:visitschedule_list')
    else:
        form = VisitScheduleForm()
    return render(request, 'homecare/visitschedule_form.html', {'form': form})

@login_required
@role_required(['admin', 'doctor'])
def visitschedule_update(request, pk):
    visit = get_object_or_404(VisitSchedule, pk=pk)
    if request.method == 'POST':
        form = VisitScheduleForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect('homecare:visitschedule_list')
    else:
        form = VisitScheduleForm(instance=visit)
    return render(request, 'homecare/visitschedule_form.html', {'form': form})

@login_required
@role_required(['admin'])
def visitschedule_delete(request, pk):
    visit = get_object_or_404(VisitSchedule, pk=pk)
    if request.method == 'POST':
        visit.delete()
        return redirect('homecare:visitschedule_list')
    return render(request, 'homecare/visitschedule_confirm_delete.html', {'visit': visit})

# -------------------------------
# Notes, Treatments, Medications, Vitals CRUD
# All have role-based visibility
# -------------------------------
def _get_queryset_for_user(model, user):
    """
    Returns a queryset filtered by the user's role and assignments:
    - Nurses see objects related to patients assigned to them.
    - Doctors see objects related to patients assigned to them.
    - Admins see all objects.
    """
    if hasattr(user, 'healthprofessional'):
        hp = user.healthprofessional
        if hp.role in ['nurse', 'doctor']:
            return model.objects.filter(patient__assignments__professional=hp).distinct()
    return model.objects.all()  # Admin or users without role

@login_required
@role_required(['admin', 'nurse'])
def nursesnote_create(request):
    if request.method == 'POST':
        form = NursesNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.created_by = request.user.healthprofessional
            note.save()
            return redirect('homecare:nursesnote_list')
    else:
        form = NursesNoteForm()
    return render(request, 'homecare/nursesnote_form.html', {'form': form})

@login_required
@role_required(['admin', 'nurse'])
def nursesnote_update(request, pk):
    note = get_object_or_404(NursesNote, pk=pk)
    if request.method == 'POST':
        form = NursesNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('homecare:nursesnote_list')
    else:
        form = NursesNoteForm(instance=note)
    return render(request, 'homecare/nursesnote_form.html', {'form': form})

@login_required
@role_required(['admin'])
def nursesnote_delete(request, pk):
    note = get_object_or_404(NursesNote, pk=pk)
    if request.method == 'POST':
        note.delete()
        return redirect('homecare:nursesnote_list')
    return render(request, 'homecare/nursesnote_confirm_delete.html', {'note': note})

# DoctorNote CRUD
@login_required
@role_required(['admin', 'doctor'])
def doctornote_list(request):
    notes = _get_queryset_for_user(DoctorNote, request.user)
    return render(request, 'homecare/doctornote_list.html', {'notes': notes})

# -------------------------------
# Patient CRUD
# -------------------------------


@login_required
@role_required(['admin', 'doctor'])
def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('homecare:patient_list')
    else:
        form = PatientForm(instance=patient)
    return render(request, 'homecare/patient_form.html', {'form': form})


@login_required
@role_required(['admin'])
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient.delete()
        return redirect('homecare:patient_list')
    return render(request, 'homecare/patient_confirm_delete.html', {'patient': patient})


# -------------------------------
# Health Professional CRUD
# -------------------------------
@login_required
@role_required(['admin'])
def professional_list(request):
    professionals = HealthProfessional.objects.all()
    return render(request, 'homecare/professional_list.html', {'professionals': professionals})


@login_required
@role_required(['admin'])
def professional_create(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        prof_form = HealthProfessionalForm(request.POST)
        if user_form.is_valid() and prof_form.is_valid():
            user = user_form.save()
            prof = prof_form.save(commit=False)
            prof.user = user
            prof.save()
            return redirect('homecare:professional_list')
    else:
        user_form = UserForm()
        prof_form = HealthProfessionalForm()
    return render(request, 'homecare/professional_form.html', {'user_form': user_form, 'prof_form': prof_form})


@login_required
@role_required(['admin'])
def professional_update(request, pk):
    prof = get_object_or_404(HealthProfessional, pk=pk)
    user = prof.user
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        prof_form = HealthProfessionalForm(request.POST, instance=prof)
        if user_form.is_valid() and prof_form.is_valid():
            user_form.save()
            prof_form.save()
            return redirect('homecare:professional_list')
    else:
        user_form = UserForm(instance=user)
        prof_form = HealthProfessionalForm(instance=prof)
    return render(request, 'homecare/professional_form.html', {'user_form': user_form, 'prof_form': prof_form})


@login_required
@role_required(['admin'])
def professional_delete(request, pk):
    prof = get_object_or_404(HealthProfessional, pk=pk)
    if request.method == 'POST':
        prof.user.delete()
        return redirect('homecare:professional_list')
    return render(request, 'homecare/professional_confirm_delete.html', {'professional': prof})


# -------------------------------
# CarePlan CRUD (with Addendum)
# -------------------------------
@login_required
@role_required(['admin', 'doctor', 'nurse'])
def careplan_list(request):
    hp = getattr(request.user, 'healthprofessional', None)
    if hp and hp.role in ['nurse', 'doctor']:
        careplans = CarePlan.objects.filter(patient__assignments__professional=hp).distinct()
    else:
        careplans = CarePlan.objects.all()
    return render(request, 'homecare/careplan_list.html', {'careplans': careplans})


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .forms import CarePlanForm
from .models import DiagnosisRecord


@login_required
@role_required(['admin', 'doctor', 'nurse'])
def careplan_create(request):
    if request.method == 'POST':
        form = CarePlanForm(request.POST, user=request.user)

        if form.is_valid():
            # Save Care Plan
            careplan = form.save(commit=False)
            careplan.created_by = request.user.healthprofessional
            careplan.save()

            # ============================
            # Save Diagnosis (if provided)
            # ============================
            diagnosis_text = form.cleaned_data.get('diagnosis')
            diagnosis_summary = form.cleaned_data.get('diagnosis_summary')

            if diagnosis_text:
                DiagnosisRecord.objects.create(
                    patient=careplan.patient,
                    diagnosis=diagnosis_text,
                    summary=diagnosis_summary or "",
                    created_by=request.user
                )

            return redirect('homecare:careplan_list')

    else:
        form = CarePlanForm(user=request.user)

    return render(request, 'homecare/careplan_form.html', {
        'form': form
    })


@login_required
@role_required(['admin', 'doctor', 'nurse'])
def careplan_update(request, pk):
    # Original care plan
    original = get_object_or_404(CarePlan, pk=pk)

    if request.method == 'POST':
        form = CarePlanForm(
            request.POST,
            instance=original,
            user=request.user
        )

        if form.is_valid():
            # ============================
            # Create CarePlan Addendum
            # ============================
            addendum = form.save(commit=False)
            addendum.pk = None                 # create new row (history preserved)
            addendum.is_addendum = True
            addendum.original = original
            addendum.created_by = getattr(request.user, 'healthprofessional', None)
            addendum.save()

            # ============================
            # Save Diagnosis (if provided)
            # ============================
            diagnosis_text = form.cleaned_data.get('diagnosis')
            diagnosis_summary = form.cleaned_data.get('diagnosis_summary')

            if diagnosis_text:
                DiagnosisRecord.objects.create(
                    patient=addendum.patient,
                    diagnosis=diagnosis_text,
                    summary=diagnosis_summary or "",
                    created_by=request.user
                )

            return redirect('homecare:careplan_list')

    else:
        form = CarePlanForm(
            instance=original,
            user=request.user
        )

    return render(request, 'homecare/careplan_form.html', {
        'form': form
    })


# -------------------------------
# VisitSchedule (view only for non-admin)
# -------------------------------
@login_required
@role_required(['admin', 'doctor', 'nurse'])
def visitschedule_list(request):
    hp = getattr(request.user, 'healthprofessional', None)
    if hp and hp.role in ['nurse', 'doctor']:
        visits = VisitSchedule.objects.filter(caregivers=hp).distinct()
    else:
        visits = VisitSchedule.objects.all()
    return render(request, 'homecare/visitschedule_list.html', {'visits': visits})


@login_required
@role_required(['admin'])
def visitschedule_create(request):
    if request.method == 'POST':
        form = VisitScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homecare:visitschedule_list')
    else:
        form = VisitScheduleForm()
    return render(request, 'homecare/visitschedule_form.html', {'form': form})


@login_required
@role_required(['admin'])
def visitschedule_update(request, pk):
    visit = get_object_or_404(VisitSchedule, pk=pk)
    if request.method == 'POST':
        form = VisitScheduleForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect('homecare:visitschedule_list')
    else:
        form = VisitScheduleForm(instance=visit)
    return render(request, 'homecare/visitschedule_form.html', {'form': form})


@login_required
@role_required(['admin'])
def visitschedule_delete(request, pk):
    visit = get_object_or_404(VisitSchedule, pk=pk)
    if request.method == 'POST':
        visit.delete()
        return redirect('homecare:visitschedule_list')
    return render(request, 'homecare/visitschedule_confirm_delete.html', {'visit': visit})


# -------------------------------
# Shared CRUD for Notes, Treatments, Medications, Vitals
# -------------------------------
def _get_queryset_for_user(model, user):
    hp = getattr(user, 'healthprofessional', None)
    if hp and hp.role in ['nurse', 'doctor']:
        return model.objects.filter(patient__assignments__professional=hp).distinct()
    return model.objects.all()


# Example for NursesNote
@login_required
@role_required(['admin', 'nurse'])
def nursesnote_list(request):
    notes = _get_queryset_for_user(NursesNote, request.user)
    return render(request, 'homecare/nursesnote_list.html', {'notes': notes})


# ======================================================
# CREATE NURSES NOTE
# ======================================================

@login_required
@role_required(['admin', 'nurse'])
def nursesnote_create(request):
    if request.method == 'POST':
        form = NursesNoteForm(request.POST, user=request.user)
        if form.is_valid():
            # Save the nurse note
            note = form.save(commit=False)
            note.created_by = request.user.healthprofessional
            note.save()

            # Automatically create or update diagnosis for this patient
            diagnosis_text = request.POST.get('diagnosis', '').strip()
            summary_text = request.POST.get('diagnosis_summary', '').strip()

            if diagnosis_text or summary_text:
                DiagnosisRecord.objects.create(
                    patient=note.patient,
                    diagnosis=diagnosis_text,
                    summary=summary_text,
                    created_by=request.user
                )

            return redirect('homecare:nursesnote_list')
    else:
        form = NursesNoteForm(user=request.user)

    return render(request, 'homecare/nursesnote_form.html', {
        'form': form
    })


# ======================================================
# UPDATE NURSES NOTE
# ======================================================

@login_required
@role_required(['admin', 'nurse'])
def nursesnote_update(request, pk):
    note = get_object_or_404(NursesNote, pk=pk)

    if request.method == 'POST':
        form = NursesNoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            updated_note = form.save()

            # Update or create diagnosis for this patient
            diagnosis_text = request.POST.get('diagnosis', '').strip()
            summary_text = request.POST.get('diagnosis_summary', '').strip()

            if diagnosis_text or summary_text:
                # Check if there is already a diagnosis record linked to this patient
                diagnosis_record, created = DiagnosisRecord.objects.get_or_create(
                    patient=updated_note.patient,
                    defaults={
                        'diagnosis': diagnosis_text,
                        'summary': summary_text,
                        'created_by': request.user
                    }
                )
                if not created:
                    # If already exists, update the fields
                    diagnosis_record.diagnosis = diagnosis_text
                    diagnosis_record.summary = summary_text
                    diagnosis_record.save()

            return redirect('homecare:nursesnote_list')
    else:
        form = NursesNoteForm(instance=note, user=request.user)

    return render(request, 'homecare/nursesnote_form.html', {
        'form': form
    })



@login_required
@role_required(['admin'])
def nursesnote_delete(request, pk):
    note = get_object_or_404(NursesNote, pk=pk)
    if request.method == 'POST':
        note.delete()
        return redirect('homecare:nursesnote_list')
    return render(request, 'homecare/nursesnote_confirm_delete.html', {'note': note})


# Similar views should be implemented for DoctorNote, TreatmentSheet, MedicationSheet, VitalSignRecord
# with _get_queryset_for_user and role-based create/update/delete as per your rules.


# -------------------------------
# Patient-specific access code
# -------------------------------
@login_required
@role_required(['admin', 'doctor'])
def generate_patient_access_code(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    patient.access_code = get_random_string(length=12)
    patient.save()
    return render(request, 'homecare/patient_access_code.html', {'patient': patient})


# -------------------------------
# Patient health tracing by code
# -------------------------------
def patient_trace_view(request):
    code = request.GET.get('code', '')
    patient = Patient.objects.filter(access_code=code).first()
    if patient:
        hp = getattr(request.user, 'healthprofessional', None)
        # Only allow if admin or doctor who created code
        if not (request.user.is_superuser or (hp and hp.role in ['doctor', 'admin'])):
            patient = None
    return render(request, 'homecare/patient_trace.html', {'patient': patient})

@login_required
@role_required(['admin', 'nurse','doctor'])
def medicationsheet_list(request):
    meds = _get_queryset_for_user(MedicationSheet, request.user)
    return render(request, 'homecare/medicationsheet_list.html', {'meds': meds})

# ======================================================
# CREATE MEDICATION SHEET
# ======================================================

@login_required
@role_required(['admin', 'nurse', 'doctor'])
def medicationsheet_create(request):
    if request.method == 'POST':
        form = MedicationSheetForm(request.POST, user=request.user)
        if form.is_valid():
            med = form.save(commit=False)
            med.created_by = request.user.healthprofessional
            med.save()
            return redirect('homecare:medicationsheet_list')
    else:
        form = MedicationSheetForm(user=request.user)

    return render(request, 'homecare/medicationsheet_form.html', {
        'form': form
    })


# ======================================================
# UPDATE MEDICATION SHEET
# ======================================================

@login_required
@role_required(['admin', 'nurse', 'doctor'])
def medicationsheet_update(request, pk):
    med = get_object_or_404(MedicationSheet, pk=pk)

    if request.method == 'POST':
        form = MedicationSheetForm(
            request.POST,
            instance=med,
            user=request.user
        )
        if form.is_valid():
            form.save()
            return redirect('homecare:medicationsheet_list')
    else:
        form = MedicationSheetForm(
            instance=med,
            user=request.user
        )

    return render(request, 'homecare/medicationsheet_form.html', {
        'form': form
    })

@login_required
@role_required(['admin'])
def medicationsheet_delete(request, pk):
    med = get_object_or_404(MedicationSheet, pk=pk)
    if request.method == 'POST':
        med.delete()
        return redirect('homecare:medicationsheet_list')
    return render(request, 'homecare/medicationsheet_confirm_delete.html', {'med': med})

# Vital signs

# VitalSignRecord CRUD
@login_required
@role_required(['admin', 'nurse', 'doctor'])
def vitalsign_list(request):
    vitals = _get_queryset_for_user(VitalSignRecord, request.user)
    return render(request, 'homecare/vitalsign_list.html', {'vitals': vitals})


@login_required
@role_required(['admin', 'nurse', 'doctor'])
def vitalsign_create(request):
    if request.method == 'POST':
        form = VitalSignRecordForm(request.POST, user=request.user)
        if form.is_valid():
            vital = form.save(commit=False)
            vital.created_by = request.user.healthprofessional
            vital.save()
            return redirect('homecare:vitalsign_list')
    else:
        form = VitalSignRecordForm(user=request.user)

    return render(request, 'homecare/vitalsign_form.html', {'form': form})

@login_required
@role_required(['admin', 'nurse', 'doctor'])
def vitalsign_update(request, pk):
    vital = get_object_or_404(VitalSignRecord, pk=pk)

    if request.method == 'POST':
        form = VitalSignRecordForm(
            request.POST or None,
            instance=vital,
            user=request.user
        )
        if form.is_valid():
            form.save()
            return redirect('homecare:vitalsign_list')
    else:
        form = VitalSignRecordForm(
            instance=vital,
            user=request.user
        )

    return render(request, 'homecare/vitalsign_form.html', {'form': form})


@login_required
@role_required(['admin'])
def vitalsign_delete(request, pk):
    vital = get_object_or_404(VitalSignRecord, pk=pk)
    if request.method == 'POST':
        vital.delete()
        return redirect('homecare:vitalsign_list')
    return render(request, 'homecare/vitalsign_confirm_delete.html', {'vital': vital})

from django.shortcuts import render

def landing_page(request):
    return render(request, 'duxthealth_frontend/index.html')

#Homecare request views

def request_homecare(request):
    if request.method == "POST":
        form = HomecareRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your homecare request has been submitted. Our team will contact you shortly."
            )
            return redirect("homecare:request_success")
    else:
        form = HomecareRequestForm()

    return render(request, "homecare/request_homecare.html", {"form": form})

#Register new patient for homecare service


def homecare_application(request):
    if request.method == "POST":
        form = HomecareApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()

            # 📧 EMAIL CONTENT
            subject = "🩺 New Homecare Service Request"
            message = f"""
New Homecare Application Received:

Name: {application.full_name}
Phone: {application.phone_number}
WhatsApp: {application.whatsapp_number}
Email: {application.email}
Location: {application.location}
Service Needed: {application.service_needed}

Message:
{application.message}
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ["duxthealth@gmail.com"],  # 🔴 CHANGE THIS
                fail_silently=False,
            )

            # 📲 WhatsApp redirect
            whatsapp_url = (
                f"https://wa.me/+233209840865"
                f"?text=Hello%20DuxtHealth,%20I%20just%20applied%20for%20homecare%20services."
            )

            return render(
                request,
                "homecare/homecare_application_form.html",
                {
                    "form": HomecareApplicationForm(),
                    "success": True,
                    "whatsapp_url": whatsapp_url,
                },
            )
    else:
        form = HomecareApplicationForm()

    return render(request, "homecare/homecare_application_form.html", {"form": form})

#Patient feedback and rating of staffs and system

@login_required
def submit_feedback(request):
    if request.method != "POST":
        return redirect("patient_dashboard:dashboard")

    # Ensure patient profile exists
    if not hasattr(request.user, "patient_profile"):
        messages.error(request, "Patient profile not found.")
        return redirect("patient_dashboard:dashboard")

    patient = request.user.patient_profile

    try:
        PatientFeedback.objects.create(
            patient=patient,
            comments=request.POST.get("comments", "").strip(),

            overall_rating=int(request.POST.get("overall_rating")),
            communication_rating=int(request.POST.get("communication_rating")),
            professionalism_rating=int(request.POST.get("professionalism_rating")),
            timeliness_rating=int(request.POST.get("timeliness_rating")),
        )
    except (TypeError, ValueError):
        messages.error(request, "Invalid rating submitted. Please try again.")
        return redirect("patient_dashboard:dashboard")

    messages.success(request, "💙 Thank you for sharing this with us. Your feedback has been received and will be reviewed by our care team. We’re here for you, and we’ll take the right steps where needed."
)
    return redirect("patient_dashboard:dashboard")

#Admin dashboard

# ======================================================
# ADMIN CHECK
# ======================================================
def is_admin(user):
    return user.is_authenticated and user.is_staff


# ======================================================
# ADMIN DASHBOARD (OVERVIEW)
# ======================================================
@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        raise PermissionDenied("Admins only")

    total_patients = Patient.objects.count()
    total_staff = HealthProfessional.objects.count()
    total_feedback = PatientFeedback.objects.count()

    low_feedbacks = PatientFeedback.objects.filter(
        overall_rating__lte=2
    ).select_related("patient").order_by("-created_at")[:5]

    avg_rating = PatientFeedback.objects.aggregate(
        avg=Avg("overall_rating")
    )["avg"] or 0

    context = {
        "total_patients": total_patients,
        "total_staff": total_staff,
        "total_feedback": total_feedback,
        "low_feedbacks": low_feedbacks,
        "avg_rating": round(avg_rating, 1),
    }

    return render(
        request,
        "homecare/admin/dashboard.html",
        context
    )


# ======================================================
# ADMIN – PATIENT LIST
# ======================================================
@login_required
def admin_patients(request):
    if not is_admin(request.user):
        raise PermissionDenied("Admins only")

    patients = Patient.objects.order_by("-created_at")

    return render(
        request,
        "homecare/admin/patients.html",
        {"patients": patients}
    )


# ======================================================
# ADMIN – SINGLE PATIENT DETAIL
# ======================================================
@login_required
@role_required(['admin', 'doctor', 'nurse'])
def admin_patient_detail(request, patient_id):
    if not is_admin(request.user):
        raise PermissionDenied("Admins only")

    patient = get_object_or_404(Patient, id=patient_id)

    feedbacks = PatientFeedback.objects.filter(
        patient=patient
    ).order_by("-created_at")

    diagnosis_history = patient.diagnosis_records.order_by("-created_at")

    context = {
        "patient": patient,
        "feedbacks": feedbacks,
        "diagnosis_history": diagnosis_history,
    }

    return render(
        request,
        "homecare/admin/patient_detail.html",
        context
    )


# ======================================================
# ADMIN – PATIENT STATUS ACTIONS
# ======================================================
@login_required
def admin_toggle_patient_status(request, patient_id):
    if not is_admin(request.user):
        raise PermissionDenied("Admins only")

    patient = get_object_or_404(Patient, id=patient_id)
    patient.is_active = not patient.is_active
    patient.save()

    if patient.is_active:
        messages.success(request, "✅ Patient account reactivated.")
    else:
        messages.warning(request, "🚫 Patient account deactivated.")

    return redirect("homecare:admin_patient_detail", patient_id=patient.id)


@login_required
def admin_flag_patient(request, patient_id):
    if not is_admin(request.user):
        raise PermissionDenied("Admins only")

    patient = get_object_or_404(Patient, id=patient_id)
    patient.is_flagged = True
    patient.save()

    messages.error(
        request,
        "⚠️ Patient flagged for administrative review."
    )

    return redirect("homecare:admin_patient_detail", patient_id=patient.id)


@login_required
def admin_unflag_patient(request, patient_id):
    if not is_admin(request.user):
        raise PermissionDenied("Admins only")

    patient = get_object_or_404(Patient, id=patient_id)
    patient.is_flagged = False
    patient.save()

    messages.success(request, "✅ Patient flag removed.")

    return redirect("homecare:admin_patient_detail", patient_id=patient.id)

# ======================================================
# ADMIN – FEEDBACK LIST
# ======================================================
@login_required
def admin_feedbacks(request):
    if not is_admin(request.user):
        raise PermissionDenied("Admins only")

    feedbacks = PatientFeedback.objects.select_related(
        "patient"
    ).order_by("-created_at")

    context = {
        "feedbacks": feedbacks,
    }

    return render(
        request,
        "homecare/admin/feedbacks.html",
        context
    )

# homecare/views.py Diagnosis

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from .models import Patient, DiagnosisRecord
from .forms import DiagnosisForm


def can_add_diagnosis(user):
    return (
        user.is_superuser or
        hasattr(user, "healthprofessional") and
        user.healthprofessional.role in ["admin", "doctor", "nurse"]
    )


@login_required
def add_diagnosis(request, patient_id):
    if not can_add_diagnosis(request.user):
        raise PermissionDenied("Not allowed")

    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == "POST":
        form = DiagnosisForm(request.POST)
        if form.is_valid():
            diagnosis_record = form.save(commit=False)
            diagnosis_record.patient = patient
            diagnosis_record.created_by = request.user
            diagnosis_record.save()

            # update patient's current diagnosis
            patient.diagnosis = diagnosis_record.diagnosis
            patient.diagnosis_summary = diagnosis_record.summary
            patient.save()

            messages.success(request, "✅ Diagnosis saved successfully.")
            return redirect("homecare:patient_detail", patient_id=patient.id)
    else:
        form = DiagnosisForm()

    return render(
        request,
        "homecare/add_diagnosis.html",
        {
            "form": form,
            "patient": patient
        }
    )

# homecare/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Patient, DiagnosisRecord
from .forms import DiagnosisForm

@login_required
def diagnosis_list(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    diagnoses = patient.diagnosis_records.order_by("-created_at")
    return render(
        request,
        "homecare/diagnosis_list.html",
        {"patient": patient, "diagnoses": diagnoses}
    )

@login_required
def diagnosis_create(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == "POST":
        diagnosis = request.POST.get("diagnosis")
        summary = request.POST.get("summary")

        if diagnosis and summary:
            DiagnosisRecord.objects.create(
                patient=patient,
                diagnosis=diagnosis,
                summary=summary,
                created_by=request.user,
            )

            # Optional: keep latest diagnosis on Patient model
            patient.diagnosis = diagnosis
            patient.diagnosis_summary = summary
            patient.save()

            return redirect(
                "homecare:diagnosis_list",
                patient_id=patient.id
            )

    return render(
        request,
        "homecare/diagnosis_form.html",
        {
            "patient": patient,
        }
    )


@login_required
def diagnosis_form(request, patient_id=None, diagnosis_id=None):
    if diagnosis_id:
        # Editing existing diagnosis
        diagnosis_record = get_object_or_404(DiagnosisRecord, id=diagnosis_id)
        patient = diagnosis_record.patient
        if not can_add_diagnosis(request.user):
            raise PermissionDenied("You cannot edit this diagnosis")
        form = DiagnosisForm(request.POST or None, instance=diagnosis_record)
    else:
        # Adding new diagnosis
        patient = get_object_or_404(Patient, id=patient_id)
        if not can_add_diagnosis(request.user):
            raise PermissionDenied("You cannot add diagnosis")
        form = DiagnosisForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        new_diag = form.save(commit=False)
        new_diag.patient = patient
        new_diag.created_by = request.user
        new_diag.save()
        messages.success(request, "✅ Diagnosis saved successfully.")
        return redirect("homecare:diagnosis_list", patient_id=patient.id)

    return render(
        request,
        "homecare/diagnosis_form.html",
        {"form": form, "patient": patient, "editing": bool(diagnosis_id)}
    )

@login_required
def diagnosis_update(request, pk):
    diagnosis_record = get_object_or_404(DiagnosisRecord, pk=pk)
    patient = diagnosis_record.patient

    if request.method == "POST":
        diagnosis_record.diagnosis = request.POST.get("diagnosis")
        diagnosis_record.summary = request.POST.get("summary")
        diagnosis_record.save()

        # Keep patient current diagnosis in sync
        patient.diagnosis = diagnosis_record.diagnosis
        patient.diagnosis_summary = diagnosis_record.summary
        patient.save()

        return redirect(
            "homecare:diagnosis_list",
            patient_id=patient.id
        )

    return render(
        request,
        "homecare/diagnosis_form.html",
        {
            "patient": patient,
            "diagnosis_record": diagnosis_record,
        }
    )


#ADMIN MANAGEING STAFFS AND NURSES AND DOCTORS

# =========================
# ADMIN – STAFF LIST
# =========================
@login_required
def admin_staff_list(request):
    if not request.user.is_staff:
        raise PermissionDenied("Admins only")

    # Latest staff first (uses newly added created_at)
    staff = (
        HealthProfessional.objects
        .select_related("user")
        .order_by("-created_at")
    )

    return render(
        request,
        "homecare/admin/staff_list.html",
        {
            "staff": staff
        }
    )


# =========================
# ADMIN – STAFF DETAIL
# =========================
@login_required
def admin_staff_detail(request, staff_id):
    if not request.user.is_staff:
        raise PermissionDenied("Admins only")

    staff = get_object_or_404(
        HealthProfessional.objects.select_related("user"),
        id=staff_id
    )

    return render(
        request,
        "homecare/admin/staff_detail.html",
        {
            "staff": staff
        }
    )


# =========================
# ADMIN – TOGGLE ACTIVE STATUS
# =========================
@login_required
def admin_toggle_staff_status(request, staff_id):
    if not request.user.is_staff:
        raise PermissionDenied("Admins only")

    staff = get_object_or_404(HealthProfessional, id=staff_id)
    staff.is_active = not staff.is_active
    staff.save(update_fields=["is_active"])

    messages.success(
        request,
        f"{staff.user.get_full_name()} status updated successfully."
    )

    return redirect(
        "homecare:admin_staff_detail",
        staff_id=staff.id
    )


# =========================
# ADMIN – FLAG STAFF
# =========================
@login_required
def admin_flag_staff(request, staff_id):
    if not request.user.is_staff:
        raise PermissionDenied("Admins only")

    staff = get_object_or_404(HealthProfessional, id=staff_id)
    staff.is_flagged = True
    staff.save(update_fields=["is_flagged"])

    messages.warning(
        request,
        f"{staff.user.get_full_name()} has been flagged for review."
    )

    return redirect(
        "homecare:admin_staff_detail",
        staff_id=staff.id
    )


# =========================
# ADMIN – UNFLAG STAFF
# =========================
@login_required
def admin_unflag_staff(request, staff_id):
    if not request.user.is_staff:
        raise PermissionDenied("Admins only")

    staff = get_object_or_404(HealthProfessional, id=staff_id)
    staff.is_flagged = False
    staff.save(update_fields=["is_flagged"])

    messages.success(
        request,
        f"Flag removed for {staff.user.get_full_name()}."
    )

    return redirect(
        "homecare:admin_staff_detail",
        staff_id=staff.id
    )

# ==========================================================
# DUXTHEALTH AI – PATIENT DETAIL VIEW (CLINICAL ENGINE)
# ==========================================================

import os
import json
import uuid

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Patient, AIConversation
from DuxtHealth_AI.ai_modules.clinical_engine import ClinicalEngine


# ==========================================================
# PATIENT DETAIL PAGE (UI + CLINICAL ENGINE)
# ==========================================================

@login_required
def patient_detail(request, patient_id):

    patient = get_object_or_404(Patient, id=patient_id)
    engine = ClinicalEngine()

    if request.method == "POST":

        user_message = request.POST.get("ai_message", "").strip()
        role = request.POST.get("role", "doctor")

        if not user_message:
            return JsonResponse({"error": "Message cannot be empty"}, status=400)

        try:
            result = engine.process(
                patient=patient,
                message=user_message,
                role=role,
                session_id=f"patient_{patient.id}"
            )

            ai_response = result.get("response", "")
            engine_used = result.get("engine_used", "clinical_engine")
            emergency_flag = result.get("emergency_detected", False)

            # Ensure clean string output
            if isinstance(ai_response, dict):
                ai_response = json.dumps(ai_response, indent=2)

            ai_response = str(ai_response).strip()

            # Emergency formatting
            if emergency_flag:
                ai_response = (
                    "🚨 EMERGENCY ALERT 🚨\n\n"
                    + ai_response +
                    "\n\nImmediate medical intervention recommended."
                )

        except Exception as e:
            ai_response = f"AI Engine Error: {str(e)}"
            engine_used = "error"
            emergency_flag = False

        # =========================
        # SAVE CONVERSATION (LEGAL LOG)
        # =========================
        AIConversation.objects.create(
            patient=patient,
            user=request.user,
            user_message=user_message,
            ai_response=ai_response,
            ip_address=request.META.get("REMOTE_ADDR"),
            timestamp=timezone.now()
        )

        # AJAX response
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "response": ai_response,
                "engine_used": engine_used,
                "emergency_detected": emergency_flag
            })

    conversations = AIConversation.objects.filter(
        patient=patient,
        user=request.user
    ).order_by("timestamp")

    return render(request, "homecare/patient_detail.html", {
        "patient": patient,
        "conversations": conversations
    })


# ==========================================================
# DIRECT AI ENDPOINT (IMAGE + PDF SUPPORT)
# ==========================================================

@csrf_exempt
@login_required
def ai_clinical_chat(request, patient_id):

    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)

    patient = get_object_or_404(Patient, id=patient_id)
    engine = ClinicalEngine()

    user_message = request.POST.get("message", "").strip()
    role = request.POST.get("role", "doctor")

    if not user_message:
        return JsonResponse({"error": "Message cannot be empty"}, status=400)

    image_path = None
    pdf_path = None

    upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # =========================
    # SAFE FILE SAVE FUNCTION
    # =========================
    def save_uploaded_file(file_obj):
        unique_name = f"{uuid.uuid4()}_{file_obj.name}"
        file_path = os.path.join(upload_dir, unique_name)

        with open(file_path, "wb+") as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        return file_path

    # Save image
    if "image" in request.FILES:
        image_path = save_uploaded_file(request.FILES["image"])

    # Save PDF
    if "pdf" in request.FILES:
        pdf_path = save_uploaded_file(request.FILES["pdf"])

    # =========================
    # PROCESS THROUGH CLINICAL ENGINE
    # =========================
    try:
        result = engine.process(
            patient=patient,
            message=user_message,
            role=role,
            session_id=f"patient_{patient.id}",
            image_path=image_path,
            pdf_path=pdf_path
        )

        ai_response = result.get("response", "")
        engine_used = result.get("engine_used", "clinical_engine")
        emergency_flag = result.get("emergency_detected", False)

        if isinstance(ai_response, dict):
            ai_response = json.dumps(ai_response, indent=2)

        ai_response = str(ai_response).strip()

        if emergency_flag:
            ai_response = (
                "🚨 EMERGENCY ALERT 🚨\n\n"
                + ai_response +
                "\n\nImmediate medical intervention recommended."
            )

        # Save conversation
        AIConversation.objects.create(
            patient=patient,
            user=request.user,
            user_message=user_message,
            ai_response=ai_response,
            ip_address=request.META.get("REMOTE_ADDR"),
            timestamp=timezone.now()
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({
        "response": ai_response,
        "engine_used": engine_used,
        "emergency_detected": emergency_flag
    })

# homecare/views.py
import markdown
from django.http import JsonResponse

def clinical_ai_chat(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == "POST":
        question = request.POST.get("ai_message")

        # 🔹 Call your Clinical AI Copilot
        ai = ClinicalAICopilot()
        ai_result = ai.ask(
            patient=patient,
            question=question,
            role="clinical_staff"
        )

        # 🔹 THIS is where ai_response exists
        raw_ai_text = ai_result["response"]

        # 🔹 Convert Markdown → HTML
        formatted_html = markdown.markdown(
            raw_ai_text,
            extensions=["extra", "nl2br", "sane_lists"]
        )

        return JsonResponse({
            "response": formatted_html
        })

###############
import os
import json
import uuid
import markdown

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Patient, AIConversation
from DuxtHealth_AI.ai_modules.clinical_engine import ClinicalEngine


# ==========================================================
# PATIENT DETAIL PAGE (UI + CLINICAL ENGINE)
# ==========================================================

@login_required
def patient_detail(request, patient_id):

    patient = get_object_or_404(Patient, id=patient_id)
    engine = ClinicalEngine()

    if request.method == "POST":

        user_message = request.POST.get("ai_message", "").strip()
        role = request.POST.get("role", "doctor")

        if not user_message:
            return JsonResponse({"error": "Message cannot be empty"}, status=400)

        try:
            result = engine.process(
                patient=patient,
                message=user_message,
                role=role,
                session_id=f"patient_{patient.id}"
            )

            raw_ai_text = result.get("response", "")
            engine_used = result.get("engine_used", "clinical_engine")
            emergency_flag = result.get("emergency_detected", False)

            # ----------------------------------
            # 🔥 MARKDOWN → HTML (THE FIX)
            # ----------------------------------
            if isinstance(raw_ai_text, dict):
                raw_ai_text = json.dumps(raw_ai_text, indent=2)

            raw_ai_text = str(raw_ai_text).strip()

            if emergency_flag:
                raw_ai_text = (
                    "## 🚨 EMERGENCY ALERT 🚨\n\n"
                    + raw_ai_text +
                    "\n\n**Immediate medical intervention recommended.**"
                )

            ai_response_html = markdown.markdown(
                raw_ai_text,
                extensions=[
                    "extra",
                    "nl2br",
                    "sane_lists"
                ]
            )

        except Exception as e:
            ai_response_html = markdown.markdown(
                f"**AI Engine Error:** {str(e)}"
            )
            engine_used = "error"
            emergency_flag = False

        # =========================
        # SAVE CONVERSATION (HTML)
        # =========================
        AIConversation.objects.create(
            patient=patient,
            user=request.user,
            user_message=user_message,
            ai_response=ai_response_html,  # ✅ HTML SAVED
            ip_address=request.META.get("REMOTE_ADDR"),
            timestamp=timezone.now()
        )

        # AJAX response
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "response": ai_response_html,  # ✅ HTML RETURNED
                "engine_used": engine_used,
                "emergency_detected": emergency_flag
            })

    conversations = AIConversation.objects.filter(
        patient=patient,
        user=request.user
    ).order_by("timestamp")

    return render(request, "homecare/patient_detail.html", {
        "patient": patient,
        "conversations": conversations
    })