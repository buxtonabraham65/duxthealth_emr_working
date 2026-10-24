from django.shortcuts import render, redirect, get_object_or_404
from .models import Patient, VitalSign, Consultation, Outreach
from .forms import PatientForm, VitalSignForm, ConsultationForm, NoteForm
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

# ✅ Dashboard/Home View
@login_required
@role_required(['admin', 'outreach_0fficer'])
def home(request):
    patient_count = Patient.objects.count()
    vitals_count = VitalSign.objects.count()
    consultation_count = Consultation.objects.count()

    return render(request, 'home.html', {
        'patient_count': patient_count,
        'vitals_count': vitals_count,
        'consultation_count': consultation_count,
    })

# ✅ Register New Patient
@login_required
@role_required(['admin', 'outreach_0fficer'])
def register_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.outreach = form.cleaned_data.get('outreach')
            patient.save()
            return redirect('patient_list')
    else:
        form = PatientForm()
    return render(request, 'patients/register.html', {'form': form})

# ✅ View All Patients
@login_required
@role_required(['admin','outreach_0fficer'])
def patient_list(request):
    patients = Patient.objects.all().order_by('-date_registered')
    return render(request, 'patients/list.html', {'patients': patients})

# ✅ Record New Vitals
@login_required
@role_required(['admin', 'outreach_0fficer'])
def add_vitals(request):
    if request.method == 'POST':
        form = VitalSignForm(request.POST)
        if form.is_valid():
            vitals = form.save(commit=False)
            vitals.recorded_by = request.user
            vitals.outreach = form.cleaned_data.get('outreach')
            vitals.save()
            return redirect('add_consultation')
    else:
        form = VitalSignForm()
    return render(request, 'vitals/add_vitals.html', {'form': form})

# ✅ View All Vitals
@login_required
@role_required(['admin', 'outreach_0fficer'])
def vitals_list(request):
    vitals = VitalSign.objects.all().order_by('-date_recorded')
    return render(request, 'vitals/list.html', {'vitals': vitals})

# ✅ Add New Consultation
@login_required
@role_required(['admin', 'outreach_0fficer'])
def add_consultation(request):
    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consult = form.save(commit=False)
            consult.created_by = request.user
            consult.outreach = form.cleaned_data.get('outreach')
            consult.save()
            return redirect('home')
    else:
        form = ConsultationForm()
    return render(request, 'consultations/add_consultation.html', {'form': form})

# ✅ View All Consultations
@login_required
@role_required(['admin', 'outreach_0fficer'])
def consultation_list(request):
    consultations = Consultation.objects.all().order_by('-created_at')
    return render(request, 'consultations/list.html', {'consultations': consultations})

# ✅ Add Notes
@login_required
@role_required(['admin', 'outreach_0fficer'])
def note(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.created_by = request.user
            note.save()
            return redirect('home')
    else:
        form = NoteForm()
    return render(request, 'patients/note.html', {'form': form})

# ✅ Detailed Outreach Report – Admin only
@staff_member_required
def detailed_outreach_report(request):
    outreach_id = request.GET.get('outreach')
    outreaches = Outreach.objects.all().order_by('-date')

    if outreach_id:
        selected_outreach = get_object_or_404(Outreach, id=outreach_id)
        patients = Patient.objects.filter(outreach=selected_outreach)
        vitals = VitalSign.objects.filter(outreach=selected_outreach)
        consultations = Consultation.objects.filter(outreach=selected_outreach)
    else:
        selected_outreach = None
        patients = Patient.objects.all()
        vitals = VitalSign.objects.all()
        consultations = Consultation.objects.all()

    context = {
        'outreaches': outreaches,
        'selected_outreach': selected_outreach,
        'patients': patients,
        'vitals': vitals,
        'consultations': consultations,
    }
    return render(request, 'reports/outreach_detailed_report.html', context)

# ✅ Anonymous Outreach Report – Admin only (For research)
@staff_member_required
def anonymous_outreach_report(request):
    outreach_id = request.GET.get('outreach_id')
    all_outreaches = Outreach.objects.all().order_by('-date')
    outreach_data = []

    if outreach_id:
        outreaches = Outreach.objects.filter(id=outreach_id)
        selected_outreach_id = int(outreach_id)
    else:
        outreaches = all_outreaches
        selected_outreach_id = None

    for outreach in outreaches:
        vitals = VitalSign.objects.filter(outreach=outreach)
        consultations = Consultation.objects.filter(outreach=outreach)

        outreach_data.append({
            'outreach': outreach,
            'vitals': vitals,
            'consultations': consultations,
        })

    context = {
        'all_outreaches': all_outreaches,
        'selected_outreach_id': selected_outreach_id,
        'outreach_data': outreach_data,
    }
    return render(request, 'reports/outreach_anonymous_report.html', context)
