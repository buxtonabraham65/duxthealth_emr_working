# ai_modules/medication_checker/checker.py

import json
import os
from typing import List, Dict

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "drug_db.json")


class MedicationChecker:
    """
    Clinical-grade Medication & Prescription Checker
    """

    def __init__(self):
        self.drug_db = self._load_or_initialize_db()

    # --------------------------------------------------
    # SAFE DATABASE LOADER
    # --------------------------------------------------

    def _load_or_initialize_db(self) -> Dict:
        """
        Loads drug_db.json safely.
        If file does not exist or is empty/corrupted,
        it auto-creates a default safe database.
        """

        default_db = {
            "aspirin": {
                "interactions": ["warfarin"],
                "safe_dosage_mg_per_day": [50, 4000]
            },
            "warfarin": {
                "interactions": ["aspirin"],
                "safe_dosage_mg_per_day": [1, 10]
            },
            "paracetamol": {
                "interactions": [],
                "safe_dosage_mg_per_day": [500, 4000]
            }
        }

        # If file doesn't exist → create it
        if not os.path.exists(DB_PATH):
            with open(DB_PATH, "w") as f:
                json.dump(default_db, f, indent=4)
            return default_db

        # If file exists → try loading safely
        try:
            with open(DB_PATH, "r") as f:
                content = f.read().strip()

                # If file is empty
                if not content:
                    raise ValueError("Empty JSON file")

                return json.loads(content)

        except (json.JSONDecodeError, ValueError):
            # If corrupted → overwrite with default
            with open(DB_PATH, "w") as f:
                json.dump(default_db, f, indent=4)
            return default_db

    # --------------------------------------------------
    # Main Validation Function
    # --------------------------------------------------

    def validate_prescriptions(
        self,
        prescriptions: List[Dict],
        patient_allergies: List[str] = None
    ) -> Dict:

        if patient_allergies is None:
            patient_allergies = []

        # Normalize to lowercase for safety
        prescriptions = [
            {
                "name": p["name"].lower(),
                "dosage_mg_per_day": p["dosage_mg_per_day"]
            }
            for p in prescriptions
        ]

        patient_allergies = [a.lower() for a in patient_allergies]

        alerts = {
            "interactions": [],
            "allergy_conflicts": [],
            "dosage_issues": [],
            "duplicates": []
        }

        drug_names = [p["name"] for p in prescriptions]

        self._check_duplicates(drug_names, alerts)
        self._check_interactions(drug_names, alerts)
        self._check_allergies(drug_names, patient_allergies, alerts)
        self._check_dosage(prescriptions, alerts)

        alerts["is_safe"] = (
            not alerts["interactions"] and
            not alerts["allergy_conflicts"] and
            not alerts["dosage_issues"]
        )

        return alerts

    # --------------------------------------------------
    # Interaction Check
    # --------------------------------------------------

    def _check_interactions(self, drug_names, alerts):
        for i, drug1 in enumerate(drug_names):
            if drug1 not in self.drug_db:
                continue

            for drug2 in drug_names[i + 1:]:
                if drug2 in self.drug_db[drug1].get("interactions", []):
                    alerts["interactions"].append(
                        f"High-risk interaction between {drug1} and {drug2}"
                    )

    # --------------------------------------------------
    # Allergy Check
    # --------------------------------------------------

    def _check_allergies(self, drug_names, allergies, alerts):
        for drug in drug_names:
            if drug in allergies:
                alerts["allergy_conflicts"].append(
                    f"Patient allergic to {drug}"
                )

    # --------------------------------------------------
    # Dosage Safety Check
    # --------------------------------------------------

    def _check_dosage(self, prescriptions, alerts):
        for prescription in prescriptions:
            drug = prescription["name"]
            dosage = prescription["dosage_mg_per_day"]

            if drug not in self.drug_db:
                alerts["dosage_issues"].append(
                    f"{drug} not found in database — verify manually."
                )
                continue

            min_dose, max_dose = self.drug_db[drug].get(
                "safe_dosage_mg_per_day",
                [0, 999999]
            )

            if dosage < min_dose:
                alerts["dosage_issues"].append(
                    f"{drug} dosage too LOW ({dosage}mg/day). Minimum is {min_dose}mg."
                )
            elif dosage > max_dose:
                alerts["dosage_issues"].append(
                    f"{drug} dosage too HIGH ({dosage}mg/day). Maximum is {max_dose}mg."
                )

    # --------------------------------------------------
    # Duplicate Prescription Check
    # --------------------------------------------------

    def _check_duplicates(self, drug_names, alerts):
        seen = set()
        for drug in drug_names:
            if drug in seen:
                alerts["duplicates"].append(
                    f"Duplicate prescription detected: {drug}"
                )
            seen.add(drug)


# --------------------------------------------------
# Standalone Testing
# --------------------------------------------------

if __name__ == "__main__":

    checker = MedicationChecker()

    test_prescriptions = [
        {"name": "Aspirin", "dosage_mg_per_day": 400},
        {"name": "Warfarin", "dosage_mg_per_day": 5},
        {"name": "Aspirin", "dosage_mg_per_day": 100}
    ]

    allergies = ["Penicillin"]

    result = checker.validate_prescriptions(
        prescriptions=test_prescriptions,
        patient_allergies=allergies
    )

    print("\nMedication Validation Result:")
    for key, value in result.items():
        print(f"{key}: {value}")
