from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from dotenv import load_dotenv

from pypdf import PdfReader

import google.generativeai as genai
import os

from database.db import SessionLocal
from database.db import engine

from database.models.history import Base, History


# ------------------------------------
# ENVIRONMENT
# ------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

# ------------------------------------
# FASTAPI APP
# ------------------------------------

app = FastAPI(
    title="AI Study Assistant"
)

# ------------------------------------
# DATABASE TABLE CREATION
# ------------------------------------

Base.metadata.create_all(bind=engine)

# ------------------------------------
# CORS
# ------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------
# REQUEST MODEL
# ------------------------------------

class NotesRequest(BaseModel):
    text: str


# ------------------------------------
# HOME
# ------------------------------------

@app.get("/")
def home():

    return {
        "message":
        "AI Study Assistant Running"
    }


# ------------------------------------
# SUMMARY
# ------------------------------------

@app.post("/summary")
def generate_summary(data: NotesRequest):

    prompt = f"""
    Summarize the following notes
    in simple bullet points:

    {data.text}
    """

    response = model.generate_content(
        prompt
    )

    summary_text = response.text

    db = SessionLocal()

    record = History(
        user_input=data.text,
        output=summary_text,
        feature="summary"
    )

    db.add(record)

    db.commit()

    db.close()

    return {
        "summary": summary_text
    }


# ------------------------------------
# QUIZ
# ------------------------------------

@app.post("/quiz")
def generate_quiz(data: NotesRequest):

    prompt = f"""
    Generate 5 MCQs from:

    {data.text}

    Include answers.
    """

    response = model.generate_content(
        prompt
    )

    quiz_text = response.text

    db = SessionLocal()

    record = History(
        user_input=data.text,
        output=quiz_text,
        feature="quiz"
    )

    db.add(record)

    db.commit()

    db.close()

    return {
        "quiz": quiz_text
    }


# ------------------------------------
# CHATBOT
# ------------------------------------

@app.post("/ask")
def ask_ai(data: NotesRequest):

    prompt = f"""
    Explain simply for an
    engineering student:

    {data.text}
    """

    response = model.generate_content(
        prompt
    )

    answer_text = response.text

    db = SessionLocal()

    record = History(
        user_input=data.text,
        output=answer_text,
        feature="chat"
    )

    db.add(record)

    db.commit()

    db.close()

    return {
        "answer": answer_text
    }


# ------------------------------------
# PDF SUMMARY
# ------------------------------------

@app.post("/pdf-summary")
async def pdf_summary(
    file: UploadFile = File(...)
):

    with open(
        file.filename,
        "wb"
    ) as f:

        f.write(
            await file.read()
        )

    reader = PdfReader(
        file.filename
    )

    text = ""

    for page in reader.pages:

        extracted = (
            page.extract_text()
        )

        if extracted:

            text += extracted

    prompt = f"""
    Summarize these notes:

    {text[:8000]}
    """

    response = model.generate_content(
        prompt
    )

    summary_text = response.text

    db = SessionLocal()

    record = History(
        user_input="PDF Upload",
        output=summary_text,
        feature="pdf-summary"
    )

    db.add(record)

    db.commit()

    db.close()

    return {
        "summary": summary_text
    }


# ------------------------------------
# HISTORY
# ------------------------------------

@app.get("/history")
def get_history():

    db = SessionLocal()

    records = (
        db.query(History)
        .all()
    )

    result = []

    for r in records:

        result.append(
            {
                "id": r.id,
                "feature": r.feature,
                "input": r.user_input,
                "output": r.output
            }
        )

    db.close()

    return result