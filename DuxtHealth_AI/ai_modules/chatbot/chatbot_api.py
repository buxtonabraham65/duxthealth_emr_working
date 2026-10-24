# DuxtHealth_AI/ai_modules/chatbot/chatbot_api.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from ...clinical_engine import ClinicalEngine


# ======================================================
# FASTAPI INITIALIZATION
# ======================================================

app = FastAPI(
    title="DuxtHealth AI Chatbot API",
    description="Integrated AI Chatbot for Medication, Scheduling and Symptom Support",
    version="1.0.0"
)

# ======================================================
# ENABLE CORS (Frontend Integration Ready)
# ======================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# INITIALIZE CHATBOT ENGINE
# ======================================================

engine = ClinicalEngine()


# ======================================================
# REQUEST MODEL
# ======================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str


# ======================================================
# RESPONSE MODEL (Optional but Professional)
# ======================================================

class ChatResponse(BaseModel):
    timestamp: str
    session_id: str
    response: dict


# ======================================================
# CHAT ENDPOINT
# ======================================================

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:
        result = chatbot.respond(
            session_id=request.session_id,
            message=request.message
        )

        return ChatResponse(
            timestamp=datetime.utcnow().isoformat(),
            session_id=request.session_id,
            response=result
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# HEALTH CHECK
# ======================================================

@app.get("/")
def health_check():
    return {
        "status": "DuxtHealth AI Chatbot running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
