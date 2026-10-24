# DuxtHealth_AI/ai_modules/notes_summarizer/summarizer.py

import os
import re
import logging
from typing import Dict
from django.conf import settings

# Optional local model import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Groq import
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_MAX_LENGTH = 150


class ClinicalNotesSummarizer:
    """
    Production-ready Clinical Notes Summarizer.

    Modes:
    - "groq" (recommended cloud AI)
    - "local" (BART fallback)
    """

    def __init__(self, mode: str = "groq"):
        self.mode = mode.lower()

        if self.mode == "groq":
            if not GROQ_AVAILABLE:
                raise ImportError("Groq package not installed")

            api_key = getattr(settings, "GROQ_API_KEY", None)
            if not api_key:
                raise EnvironmentError("GROQ_API_KEY not set in Django settings")

            self.client = Groq(api_key=api_key)
            logger.info("Using Groq LLM for summarization")

        elif self.mode == "local":
            if not TRANSFORMERS_AVAILABLE:
                raise ImportError("Transformers not installed")

            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn"
            )
            logger.info("Using local BART summarization")

        else:
            raise ValueError("Mode must be 'groq' or 'local'")

    # --------------------------------------------------
    # Main Summarization
    # --------------------------------------------------

    def summarize(self, note_text: str) -> str:
        if not note_text or not note_text.strip():
            return "No content to summarize."

        if self.mode == "groq":
            return self._summarize_groq(note_text)

        return self._summarize_local(note_text)

    # --------------------------------------------------
    # Groq Summarization
    # --------------------------------------------------

    def _summarize_groq(self, text: str) -> str:

        prompt = f"""
You are a senior clinical documentation AI assistant.

Summarize the following clinical note in under {DEFAULT_MAX_LENGTH} words.

Focus strictly on:
- Diagnosis
- Current condition
- Treatment plan
- Medication changes
- Follow-up instructions

Be concise, structured, and clinically precise.

Clinical Note:
{text}
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a clinical summarization expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )

            summary = response.choices[0].message.content.strip()
            return " ".join(summary.split()[:DEFAULT_MAX_LENGTH])

        except Exception as e:
            logger.error(f"Groq summarization error: {e}")
            return "AI summarization failed. Please try again."

    # --------------------------------------------------
    # Local Transformer Summarization
    # --------------------------------------------------

    def _summarize_local(self, text: str) -> str:
        summary = self.summarizer(
            text,
            max_length=DEFAULT_MAX_LENGTH,
            min_length=60,
            do_sample=False
        )
        return summary[0]["summary_text"]

    # --------------------------------------------------
    # Structured Clinical Extraction
    # --------------------------------------------------

    def extract_key_information(self, note_text: str) -> Dict[str, str]:
        return {
            "diagnosis": self._extract_section(
                note_text,
                r"(diagnosis|dx)[:\-]\s*([\s\S]*?)(?:\n[A-Z][a-z]+:|$)"
            ),
            "medications": self._extract_section(
                note_text,
                r"(medications?|rx)[:\-]\s*([\s\S]*?)(?:\n[A-Z][a-z]+:|$)"
            ),
            "plan": self._extract_section(
                note_text,
                r"(plan|treatment plan)[:\-]\s*([\s\S]*?)(?:\n[A-Z][a-z]+:|$)"
            ),
            "vitals": self._extract_section(
                note_text,
                r"(vitals?)[:\-]\s*([\s\S]*?)(?:\n[A-Z][a-z]+:|$)"
            )
        }

    def _extract_section(self, text: str, pattern: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(2).strip() if match else "Not specified"


# --------------------------------------------------
# ✅ BACKWARD-COMPATIBILITY ALIAS (IMPORTANT)
# --------------------------------------------------

NoteSummarizer = ClinicalNotesSummarizer


# --------------------------------------------------
# Standalone Testing
# --------------------------------------------------

if __name__ == "__main__":
    example_note = """
Diagnosis: Hypertension and mild pneumonia.
Vitals: BP 150/95, HR 102, O2 91%.
Medications: Lisinopril 10mg daily, Azithromycin 500mg.
Plan: Continue antibiotics, monitor oxygen, follow-up in 3 days.
"""

    summarizer = ClinicalNotesSummarizer(mode="groq")
    print("SUMMARY:\n", summarizer.summarize(example_note))
    print("\nEXTRACTED DATA:\n", summarizer.extract_key_information(example_note))
