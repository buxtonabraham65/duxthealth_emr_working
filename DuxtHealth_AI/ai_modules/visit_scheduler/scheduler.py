# Placeholder for ai_modules/visit_scheduler/scheduler.py
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


class VisitScheduler:
    """
    Intelligent Visit Scheduler Optimizer
    """

    def __init__(self):
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError("config.json not found")

        with open(CONFIG_PATH, "r") as f:
            self.config = json.load(f)

        self.slot_duration = self.config["slot_duration_minutes"]
        self.max_patients = self.config["max_patients_per_slot"]
        self.start_time = self.config["working_hours"]["start"]
        self.end_time = self.config["working_hours"]["end"]
        self.weekend_closed = self.config["weekend_closed"]

    # --------------------------------------------------
    # PUBLIC FUNCTION
    # --------------------------------------------------

    def schedule_visit(
        self,
        requested_datetime: str,
        existing_appointments: List[Dict]
    ) -> Dict:
        """
        requested_datetime format: '2026-02-15 09:30'
        existing_appointments format:
        [
            {"datetime": "2026-02-15 09:30"},
            {"datetime": "2026-02-15 10:00"}
        ]
        """

        request_dt = datetime.strptime(requested_datetime, "%Y-%m-%d %H:%M")

        validation = self._validate_datetime(request_dt)
        if not validation["valid"]:
            return validation

        if self._is_slot_available(request_dt, existing_appointments):
            return {
                "scheduled": True,
                "scheduled_time": requested_datetime,
                "message": "Appointment successfully scheduled."
            }

        # If not available → suggest next slot
        next_slot = self._find_next_available_slot(
            request_dt,
            existing_appointments
        )

        return {
            "scheduled": False,
            "requested_time": requested_datetime,
            "suggested_time": next_slot.strftime("%Y-%m-%d %H:%M"),
            "message": "Requested slot unavailable. Suggested next available slot."
        }

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def _validate_datetime(self, dt: datetime) -> Dict:

        # Weekend check
        if self.weekend_closed and dt.weekday() >= 5:
            return {
                "valid": False,
                "message": "Clinic closed on weekends."
            }

        # Working hours check
        start_dt = datetime.strptime(
            dt.strftime("%Y-%m-%d") + " " + self.start_time,
            "%Y-%m-%d %H:%M"
        )
        end_dt = datetime.strptime(
            dt.strftime("%Y-%m-%d") + " " + self.end_time,
            "%Y-%m-%d %H:%M"
        )

        if not (start_dt <= dt < end_dt):
            return {
                "valid": False,
                "message": "Requested time outside working hours."
            }

        # Slot alignment check
        if dt.minute % self.slot_duration != 0:
            return {
                "valid": False,
                "message": f"Appointments must align with {self.slot_duration}-minute slots."
            }

        return {"valid": True}

    # --------------------------------------------------
    # CHECK SLOT AVAILABILITY
    # --------------------------------------------------

    def _is_slot_available(self, dt: datetime, existing_appointments: List[Dict]) -> bool:

        count = 0
        for appt in existing_appointments:
            existing_dt = datetime.strptime(appt["datetime"], "%Y-%m-%d %H:%M")
            if existing_dt == dt:
                count += 1

        return count < self.max_patients

    # --------------------------------------------------
    # FIND NEXT AVAILABLE SLOT
    # --------------------------------------------------

    def _find_next_available_slot(self, dt: datetime, existing_appointments: List[Dict]) -> datetime:

        current = dt

        while True:
            current += timedelta(minutes=self.slot_duration)

            # Skip weekends if closed
            if self.weekend_closed and current.weekday() >= 5:
                current = self._next_weekday_morning(current)
                continue

            # Check working hours
            if not self._within_working_hours(current):
                current = self._next_day_morning(current)
                continue

            if self._is_slot_available(current, existing_appointments):
                return current

    # --------------------------------------------------
    # HELPERS
    # --------------------------------------------------

    def _within_working_hours(self, dt: datetime) -> bool:
        start_dt = datetime.strptime(
            dt.strftime("%Y-%m-%d") + " " + self.start_time,
            "%Y-%m-%d %H:%M"
        )
        end_dt = datetime.strptime(
            dt.strftime("%Y-%m-%d") + " " + self.end_time,
            "%Y-%m-%d %H:%M"
        )
        return start_dt <= dt < end_dt

    def _next_day_morning(self, dt: datetime) -> datetime:
        next_day = dt + timedelta(days=1)
        while self.weekend_closed and next_day.weekday() >= 5:
            next_day += timedelta(days=1)

        return datetime.strptime(
            next_day.strftime("%Y-%m-%d") + " " + self.start_time,
            "%Y-%m-%d %H:%M"
        )

    def _next_weekday_morning(self, dt: datetime) -> datetime:
        next_day = dt
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)

        return datetime.strptime(
            next_day.strftime("%Y-%m-%d") + " " + self.start_time,
            "%Y-%m-%d %H:%M"
        )


# --------------------------------------------------
# STANDALONE TEST
# --------------------------------------------------

if __name__ == "__main__":

    scheduler = VisitScheduler()

    existing = [
        {"datetime": "2026-02-16 09:00"},
        {"datetime": "2026-02-16 09:30"},
        {"datetime": "2026-02-16 10:00"}
    ]

    result = scheduler.schedule_visit(
        requested_datetime="2026-02-16 09:30",
        existing_appointments=existing
    )

    print("\nScheduler Result:")
    for k, v in result.items():
        print(f"{k}: {v}")
