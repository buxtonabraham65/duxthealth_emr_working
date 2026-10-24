# ==========================================================
# DUXHEALTH AI – CLINICAL AI COPILOT (GROQ CLOUD ENGINE)
# ==========================================================

import os
import json
from datetime import datetime
from groq import Groq
from pypdf import PdfReader

from homecare.models import (
    DiagnosisRecord,
    VitalSignRecord,
    Allergy,
    MedicationSheet,
    MedicationSchedule,
    MedicationAdministration,
    MedicationReaction,
    LabResult,
    DoctorNote,
    NursesNote,
    CarePlan,
    EmergencyContact,
)

# ==========================================================
# CLINICAL AI COPILOT
# ==========================================================

class ClinicalAICopilot:

    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = "openai/gpt-oss-20b"
        self.sessions = {}

    # ======================================================
    # MAIN ENTRY
    # ======================================================

    def ask(
        self,
        patient,
        question: str,
        role: str = "clinical_staff",
        pdf_path: str = None,
        session_id: str = None,
    ):

        if not session_id:
            session_id = f"patient_{patient.id}"

        if session_id not in self.sessions:
            self.sessions[session_id] = []

        emr_context = self.build_emr_context(patient)
        system_prompt = self._build_system_prompt(role)

        pdf_text = ""
        if pdf_path and os.path.exists(pdf_path):
            pdf_text = self._extract_pdf_text(pdf_path)

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
PATIENT EMR CONTEXT (SOURCE OF TRUTH):
{json.dumps(emr_context, indent=2)}

ATTACHED DOCUMENT:
{pdf_text if pdf_text else "No document attached."}

CLINICAL QUESTION:
{question}

RULES:
- Use ONLY the EMR context above
- If information is missing, say: "Information not available in EMR."
- Do NOT invent diagnoses or vitals
- Be concise, structured, and clinically accurate
"""
            }
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
            )
            response = completion.choices[0].message.content.strip()

        except Exception as e:
            return {
                "response": f"Groq API Error: {str(e)}",
                "engine_used": "groq_error",
                "emergency_detected": False,
            }

        emergency_flag = self._detect_emergency(response)

        self.sessions[session_id].append(
            {"question": question, "answer": response}
        )
        self.sessions[session_id] = self.sessions[session_id][-10:]

        return {
            "response": response,
            "engine_used": "groq_llama3",
            "emergency_detected": emergency_flag,
        }

    # ======================================================
    # EMR CONTEXT BUILDER (CORE FIX)
    # ======================================================

    def build_emr_context(self, patient):

        def safe(val):
            if val is None:
                return None
            if isinstance(val, (datetime,)):
                return val.isoformat()
            return str(val)

        # ---------------------------
        # Identity
        # ---------------------------
        identity = {
            "full_name": patient.full_name,
            "age": patient.age,
            "gender": patient.get_gender_display(),
            "nationality": patient.nationality,
            "primary_language": patient.primary_language,
        }

        # ---------------------------
        # Diagnosis (TIMELINE-BASED)
        # ---------------------------
        diagnoses_qs = DiagnosisRecord.objects.filter(
            patient=patient,
            is_active=True
        ).order_by("-created_at")

        active_diagnosis = None
        diagnosis_history = []

        for d in diagnoses_qs:
            diagnosis_history.append({
                "diagnosis": d.diagnosis,
                "summary": d.summary,
                "date": safe(d.created_at),
            })

        if diagnoses_qs.exists():
            latest = diagnoses_qs.first()
            active_diagnosis = {
                "diagnosis": latest.diagnosis,
                "summary": latest.summary,
                "date": safe(latest.created_at),
            }

        
        # ---------------------------
        # VITAL SIGNS (LATEST + CLINICAL OBSERVATIONS)
        # ---------------------------
        vitals = None

        latest_vitals = (
            VitalSignRecord.objects
            .filter(patient=patient)
            .select_related("recorded_by", "care_plan", "visit")
            .order_by("-recorded_at")
            .first()
        )

        if latest_vitals:
            # Calculate total GCS only when all three components exist.
            gcs_components = [
                latest_vitals.neuro_gcs_eye,
                latest_vitals.neuro_gcs_verbal,
                latest_vitals.neuro_gcs_motor,
            ]

            gcs_total = (
                sum(gcs_components)
                if all(value is not None for value in gcs_components)
                else None
            )

            # Fluid balance is calculated only when all relevant
            # intake and output measurements have been recorded.
            intake_values = [
                latest_vitals.fluid_intake_oral,
                latest_vitals.fluid_intake_iv,
                latest_vitals.fluid_intake_tube,
            ]

            output_values = [
                latest_vitals.fluid_output_urine,
                latest_vitals.fluid_output_stool,
                latest_vitals.fluid_output_vomit,
                latest_vitals.fluid_output_drains,
            ]

            total_fluid_intake = (
                sum(intake_values)
                if all(value is not None for value in intake_values)
                else None
            )

            total_fluid_output = (
                sum(output_values)
                if all(value is not None for value in output_values)
                else None
            )

            fluid_balance = (
                total_fluid_intake - total_fluid_output
                if (
                    total_fluid_intake is not None
                    and total_fluid_output is not None
                )
                else None
            )

            # BMI is calculated only when both measurements
            # are present and valid. The model stores these as
            # whole-number values; confirm the units are kg and cm.
            bmi = None

            if (
                latest_vitals.weight is not None
                and latest_vitals.height is not None
                and latest_vitals.weight > 0
                and latest_vitals.height > 0
            ):
                height_m = latest_vitals.height / 100
                bmi = round(
                    latest_vitals.weight / (height_m ** 2),
                    2,
                )

            vitals = {
                "recorded_at": safe(latest_vitals.recorded_at),

                "recorded_by": (
                    str(latest_vitals.recorded_by)
                    if latest_vitals.recorded_by_id
                    else None
                ),

                # Temperature and circulation
                "temperature": safe(latest_vitals.temperature),
                "pulse": safe(latest_vitals.pulse),
                "respiratory_rate": safe(
                    latest_vitals.respiratory_rate
                ),

                "blood_pressure": {
                    "systolic": safe(
                        latest_vitals.blood_pressure_systolic
                    ),
                    "diastolic": safe(
                        latest_vitals.blood_pressure_diastolic
                    ),
                },

                "oxygen_saturation": safe(
                    latest_vitals.oxygen_saturation
                ),

                # Blood glucose
                "blood_sugar_fbs": safe(
                    latest_vitals.blood_sugar_fbs
                ),
                "blood_sugar_rbs": safe(
                    latest_vitals.blood_sugar_rbs
                ),

                # Pain assessment
                "pain_score": safe(latest_vitals.pain_score),

                # Anthropometric measurements
                "weight": safe(latest_vitals.weight),
                "height": safe(latest_vitals.height),
                "bmi_calculated": bmi,

                # Fluid intake
                "fluid_intake": {
                    "oral": safe(latest_vitals.fluid_intake_oral),
                    "iv": safe(latest_vitals.fluid_intake_iv),
                    "tube": safe(latest_vitals.fluid_intake_tube),
                    "total": total_fluid_intake,
                },

                # Fluid output
                "fluid_output": {
                    "urine": safe(
                        latest_vitals.fluid_output_urine
                    ),
                    "stool": safe(
                        latest_vitals.fluid_output_stool
                    ),
                    "vomit": safe(
                        latest_vitals.fluid_output_vomit
                    ),
                    "drains": safe(
                        latest_vitals.fluid_output_drains
                    ),
                    "total": total_fluid_output,
                },

                "fluid_balance": fluid_balance,

                # Neurological assessment
                "neurological_assessment": {
                    "gcs_eye": safe(
                        latest_vitals.neuro_gcs_eye
                    ),
                    "gcs_verbal": safe(
                        latest_vitals.neuro_gcs_verbal
                    ),
                    "gcs_motor": safe(
                        latest_vitals.neuro_gcs_motor
                    ),
                    "gcs_total": gcs_total,
                    "avpu": latest_vitals.neuro_avpu,
                },
            }

        # ---------------------------
        # Allergies
        # ---------------------------
        allergies = []
        for a in Allergy.objects.filter(patient=patient):
            allergies.append({
                "type": a.get_allergy_type_display(),
                "substance": a.substance,
                "reaction": a.reaction,
                "severity": a.severity,
            })

        # ---------------------------
        # MEDICATIONS
        # Current prescriptions + medication history
        # + schedules + administration records + reactions
        # ---------------------------

        medications = []

        medication_qs = (
            MedicationSheet.objects
            .filter(patient=patient)
            .select_related("care_plan", "created_by")
            .prefetch_related(
                "schedules",
                "administration_records__administered_by",
                "administration_records__schedule",
                "reaction_records__recorded_by",
                "reaction_records__administration",
            )
            .order_by("-created_at")
        )

        for m in medication_qs:

            # Scheduled administration times
            schedules = []

            for schedule in m.schedules.all():
                schedules.append({
                    "scheduled_time": safe(schedule.scheduled_time),
                    "is_active": schedule.is_active,
                    "instructions": schedule.instructions,
                })

            # Actual recorded dose outcomes
            administration_records = []

            for record in m.administration_records.all():
                administration_records.append({
                    "status": record.status,
                    "status_display": record.get_status_display(),
                    "scheduled_for": safe(record.scheduled_for),
                    "administered_at": safe(record.administered_at),
                    "dose_given": record.dose_given,
                    "route_used": record.route_used,
                    "administered_by": (
                        str(record.administered_by)
                        if record.administered_by_id else None
                    ),
                    "reason_not_given": record.reason_not_given,
                    "notes": record.notes,
                    "recorded_at": safe(record.recorded_at),
                })

            # Medication reactions and follow-up
            reactions = []

            for reaction in m.reaction_records.all():
                reactions.append({
                    "observed_at": safe(reaction.observed_at),
                    "description": reaction.description,
                    "severity": reaction.severity,
                    "severity_display": reaction.get_severity_display(),
                    "action_taken": reaction.action_taken,
                    "clinician_notified": reaction.clinician_notified,
                    "follow_up_notes": reaction.follow_up_notes,
                    "recorded_by": (
                        str(reaction.recorded_by)
                        if reaction.recorded_by_id else None
                    ),
                    "recorded_at": safe(reaction.recorded_at),
                    "administration_id": reaction.administration_id,
                })

            medications.append({
                "medication_id": m.pk,
                "name": m.medication_name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "route": m.route,

                # Prescription lifecycle
                "status": m.status,
                "status_display": m.get_status_display(),
                "start_date": safe(m.start_date),
                "end_date": safe(m.end_date),
                "completed_at": safe(m.completed_at),
                "completion_notes": m.completion_notes,
                "prescription_notes": m.notes,
                "created_at": safe(m.created_at),

                # Associated clinical records
                "schedules": schedules,
                "administration_records": administration_records,
                "reactions": reactions,
            })


        # ---------------------------
        # Labs
        # ---------------------------
        labs = []
        for lab in LabResult.objects.filter(patient=patient):
            labs.append({
                "title": lab.title,
                "result_text": lab.result_text,
                "date": safe(lab.created_at),
            })

        # ---------------------------
        # Clinical Notes (Recent)
        # ---------------------------
        doctor_notes = [
            {"note": n.note, "date": safe(n.created_at)}
            for n in DoctorNote.objects.filter(patient=patient).order_by("-created_at")[:3]
        ]

        nurse_notes = [
            {"note": n.note, "date": safe(n.created_at)}
            for n in NursesNote.objects.filter(patient=patient).order_by("-created_at")[:3]
        ]

        # ---------------------------
        # Care Plans
        # ---------------------------
        care_plans = []
        care_plan_queryset = (
            CarePlan.objects
            .filter(patient=patient)
            .select_related("created_by")
            .order_by("-created_at", "-pk")
        )

        status_labels = dict(CarePlan.STATUS_CHOICES)

        for cp in care_plan_queryset:
            # A care plan is current only if it is active and ongoing.
            is_current = (cp.is_active and cp.status == "ongoing")

            # All other plans are treated as historical context.
            is_historical = not is_current

            care_plans.append({
                # Identification
                "id": cp.pk,
                "title": cp.title or "",

                # Clinical information
                "problem": cp.problem or "",
                "objective": cp.objective or "",
                "intervention": cp.intervention or "",
                "rationale": cp.rational or "",
                "evaluation": cp.evaluation or "",
                "description": cp.description or "",

                # Dates
                "start_date": (cp.start_date.isoformat() if cp.start_date else None),
                "end_date": (cp.end_date.isoformat() if cp.end_date else None),
                "created_at": (cp.created_at.isoformat() if cp.created_at else None),
                "closed_at": (cp.closed_at.isoformat() if cp.closed_at else None),

                # Outcome and status
                "status": cp.status,
                "status_label": status_labels.get(cp.status,cp.status.replace("_", " ").title()),

                "closure_notes": cp.closure_notes or "",
                # Current and historical classification
                "active": cp.is_active,
                "is_current": is_current,
                "is_historical": is_historical,

                 # Clinical AI interpretation
                "clinical_context": (
                    "Current ongoing care plan"
                    if is_current
                    else (
                        "Historical care plan. Consider its documented "
                        "outcomes and dates, but do not assume it remains active."
                    )
                ),
            })






        care_plans = []
        for cp in CarePlan.objects.filter(patient=patient):
            care_plans.append({
                "title": cp.title,
                "problem": cp.problem,
                "objective": cp.objective,
                "intervention": cp.intervention,
                "evaluation": cp.evaluation,
                "active": cp.is_active,
            })


        # ---------------------------
        # Emergency Contacts
        # ---------------------------
        emergency_contacts = []
        for ec in EmergencyContact.objects.filter(patient=patient):
            emergency_contacts.append({
                "name": ec.name,
                "relationship": ec.relationship,
                "phone": ec.phone_number,
            })

        # ---------------------------
        # FINAL EMR CONTEXT
        # ---------------------------
        return {
            "identity": identity,
            "active_diagnosis": active_diagnosis,
            "diagnosis_history": diagnosis_history,
            "medical_history": patient.medical_history,
            "vitals_latest": vitals,
            "allergies": allergies,
            "medications": medications,
            "lab_results": labs,
            "doctor_notes_recent": doctor_notes,
            "nurse_notes_recent": nurse_notes,
            "care_plans": care_plans,
            "emergency_contacts": emergency_contacts,
        }

    # ======================================================
    # ROLE PROMPTS
    # ======================================================

    def _build_system_prompt(self, role):

        if role in ["clinical_staff", "doctor"]:
            return """
You are a Clinical Decision Support AI integrated into a hospital EMR.

Follow this structure strictly:

Clinical Summary:
Assessment:
Differential Diagnosis:
Recommended Actions:
Monitoring Plan:
Red Flags:

Rules:
- Base everything ONLY on EMR data
- If unsure or missing data, say "Information not available in EMR."
"""

        if role == "patient":
            return """
You are a patient education assistant.
Explain simply.
Do not diagnose.
Encourage hospital follow-up.
"""

        if role == "admin":
            return """
You are a healthcare analytics assistant.
Focus on risk, trends, and safety indicators.
"""

        return "You are a clinical assistant."

    # ======================================================
    # PDF EXTRACTOR
    # ======================================================

    def _extract_pdf_text(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text[:4000]
        except Exception:
            return "Unable to extract PDF content."

    # ======================================================
    # EMERGENCY DETECTION
    # ======================================================

    def _detect_emergency(self, text):

        keywords = [
            "cardiac arrest",
            "stroke",
            "sepsis",
            "respiratory failure",
            "anaphylaxis",
            "life threatening",
            "critical",
            "unstable",
        ]

        return any(k in text.lower() for k in keywords)
