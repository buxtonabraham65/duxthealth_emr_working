import os
import re
from django.conf import settings
from groq import Groq

# Import internal modules
from .clinical_copilot import ClinicalAICopilot
from .notes_summarizer.summarizer import NoteSummarizer
from .medication_checker.checker import MedicationChecker
from .visit_scheduler.scheduler import VisitScheduler


# ==============================
# GROQ CLIENT INITIALIZATION
# ==============================

client = Groq(api_key=settings.GROQ_API_KEY)


class ClinicalEngine:

    def __init__(self):
        self.copilot = ClinicalAICopilot()
        self.summarizer = NoteSummarizer()
        self.med_checker = MedicationChecker()
        self.scheduler = VisitScheduler()

    # ==========================================================
    # MAIN ENTRY POINT
    # ==========================================================

    def process(self, patient, message, role="doctor", session_id=None):

        message_lower = message.lower()

        # 1️⃣ EMERGENCY DETECTION
        emergency = self._detect_emergency(message_lower)

        # 2️⃣ ROUTING DECISION
        if "summarize" in message_lower:
            return self._handle_summary(patient)

        if "schedule" in message_lower or "appointment" in message_lower:
            return self._handle_schedule(message)

        if any(drug in message_lower for drug in ["aspirin", "warfarin", "metformin", "ibuprofen"]):
            return self._handle_medication(message)

        # 3️⃣ DEFAULT → CLINICAL AI COPILOT (Groq powered)
        result = self.copilot.ask(
            patient=patient,
            question=message,
            role=role
        )

        result["engine_used"] = "clinical_copilot_groq"
        result["emergency_detected"] = emergency

        return result

    # ==========================================================
    # EMERGENCY DETECTION
    # ==========================================================

    def _detect_emergency(self, message):

        emergency_keywords = [
            "cannot breathe",
            "not breathing",
            "unconscious",
            "no pulse",
            "chest pain",
            "severe bleeding",
            "stroke",
            "seizure"
        ]

        for word in emergency_keywords:
            if word in message:
                return True

        return False

    # ==========================================================
    # SUMMARIZER HANDLER
    # ==========================================================

    def _handle_summary(self, patient):

        summary = self.summarizer.summarize(
            text=patient.medical_history or ""
        )

        return {
            "response": summary,
            "engine_used": "notes_summarizer",
            "emergency_detected": False
        }

    # ==========================================================
    # MEDICATION HANDLER
    # ==========================================================

    def _handle_medication(self, message):

        drugs = ["aspirin", "warfarin", "ibuprofen", "metformin"]
        detected = [d.capitalize() for d in drugs if d in message.lower()]

        prescriptions = [
            {"name": drug, "dosage_mg_per_day": 100}
            for drug in detected
        ]

        result = self.med_checker.validate_prescriptions(
            prescriptions=prescriptions,
            patient_allergies=[]
        )

        return {
            "response": result,
            "engine_used": "medication_checker",
            "emergency_detected": False
        }

    # ==========================================================
    # SCHEDULER HANDLER
    # ==========================================================

    def _handle_schedule(self, message):

        date_match = re.search(r"\d{4}-\d{2}-\d{2}", message)

        if not date_match:
            return {
                "response": "Please provide date in format YYYY-MM-DD.",
                "engine_used": "visit_scheduler",
                "emergency_detected": False
            }

        date_str = date_match.group()
        requested_datetime = f"{date_str} 09:00"

        result = self.scheduler.schedule_visit(
            requested_datetime=requested_datetime,
            existing_appointments=[]
        )

        return {
            "response": result,
            "engine_used": "visit_scheduler",
            "emergency_detected": False
        }
