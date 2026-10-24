import json
import os
import re

# Import integrated modules
from ...ai_modules.medication_checker.checker import MedicationChecker

from ...ai_modules.visit_scheduler.scheduler import VisitScheduler

BASE_DIR = os.path.dirname(__file__)
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")
KB_PATH = os.path.join(BASE_DIR, "knowledge_base.json")


class HealthcareChatbot:

    def __init__(self):
        with open(INTENTS_PATH, "r") as f:
            self.intents = json.load(f)

        with open(KB_PATH, "r") as f:
            self.knowledge = json.load(f)

        self.sessions = {}

        # Initialize integrated modules
        self.med_checker = MedicationChecker()
        self.scheduler = VisitScheduler()

    # =====================================================
    # MAIN RESPONSE FUNCTION
    # =====================================================

    def respond(self, session_id: str, message: str):

        message_lower = message.lower()
        intent = self._detect_intent(message_lower)

        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "appointments": []
            }

        if intent == "greeting":
            return {"response": "Hello! How can I assist you today?"}

        elif intent == "medication":
            return self._handle_medication(message_lower)

        elif intent == "appointment":
            return self._handle_appointment(session_id, message_lower)

        elif intent == "symptom":
            return self._handle_symptom(message_lower)

        elif intent == "goodbye":
            return {"response": "Goodbye. Stay healthy!"}

        return {"response": "I'm not sure I understand. Could you clarify?"}

    # =====================================================
    # INTENT DETECTION
    # =====================================================

    def _detect_intent(self, message):
        for intent, keywords in self.intents.items():
            for word in keywords:
                if word in message:
                    return intent
        return None

    # =====================================================
    # MEDICATION CHECKER INTEGRATION
    # =====================================================

    def _handle_medication(self, message):

        drugs = ["aspirin", "warfarin", "ibuprofen", "metformin", "lisinopril"]
        detected = [d.capitalize() for d in drugs if d in message]

        if len(detected) >= 1:

            prescriptions = [
                {"name": drug, "dosage_mg_per_day": 100}
                for drug in detected
            ]

            result = self.med_checker.validate_prescriptions(
                prescriptions=prescriptions,
                patient_allergies=[]
            )

            if result["is_safe"]:
                return {
                    "response": f"No major safety issues detected for {', '.join(detected)}.",
                    "details": result
                }
            else:
                return {
                    "response": "Warning: Potential medication safety issues detected.",
                    "details": result
                }

        return {"response": "Please specify medication names."}

    # =====================================================
    # VISIT SCHEDULER INTEGRATION
    # =====================================================

    def _handle_appointment(self, session_id, message):

        date_match = re.search(r"\d{4}-\d{2}-\d{2}", message)

        if not date_match:
            return {"response": "Please provide date in format YYYY-MM-DD."}

        date_str = date_match.group()
        requested_datetime = f"{date_str} 09:00"

        existing = self.sessions[session_id]["appointments"]

        result = self.scheduler.schedule_visit(
            requested_datetime=requested_datetime,
            existing_appointments=existing
        )

        if result.get("scheduled"):
            self.sessions[session_id]["appointments"].append(
                {"datetime": result["scheduled_time"]}
            )

        return result

    # =====================================================
    # SYMPTOM HANDLER
    # =====================================================

    def _handle_symptom(self, message):

        for symptom, advice in self.knowledge.items():
            if symptom in message:
                return {
                    "response": advice,
                    "symptom_detected": symptom
                }

        return {"response": "Please describe your symptoms more clearly."}
