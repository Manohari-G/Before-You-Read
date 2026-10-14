import logging
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag.llm import GeminiLLM, GeminiServiceError
from rag.prompts import build_prompt
from rag.retriever import context_from_documents, retrieve

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("before_you_read")

app = FastAPI(title="Before You Read API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SpoilerMode = Literal["NO_SPOILERS", "LIGHT_SPOILERS", "FULL_DISCUSSION"]


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    spoiler_mode: SpoilerMode = "NO_SPOILERS"
    history: list[HistoryItem] = Field(default_factory=list, max_length=12)


class RecommendRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1500)
    spoiler_mode: SpoilerMode = "NO_SPOILERS"
    history: list[HistoryItem] = Field(default_factory=list, max_length=12)


class BeforeReadRequest(BaseModel):
    book: str = Field(min_length=1, max_length=200)
    spoiler_mode: SpoilerMode = "NO_SPOILERS"
    history: list[HistoryItem] = Field(default_factory=list, max_length=12)


class CompareRequest(BaseModel):
    book1: str = Field(min_length=1, max_length=200)
    book2: str = Field(min_length=1, max_length=200)
    spoiler_mode: SpoilerMode = "NO_SPOILERS"
    history: list[HistoryItem] = Field(default_factory=list, max_length=12)


class Preferences(BaseModel):
    genres: list[str] = Field(default_factory=list)
    length: str = "Any"
    difficulty: str = "Any"
    what_you_want: list[str] = Field(default_factory=list)


class PreferenceRecommendRequest(BaseModel):
    preferences: Preferences
    spoiler_mode: SpoilerMode = "NO_SPOILERS"


_llm: GeminiLLM | None = None


def get_llm() -> GeminiLLM:
    global _llm
    if _llm is None:
        _llm = GeminiLLM()
    return _llm


def history_text(history: list[HistoryItem]) -> str:
    if not history:
        return ""
    return "\n".join(f"{item.role.upper()}: {item.content}" for item in history[-8:])


def run_rag(question: str, spoiler_mode: SpoilerMode, history: list[HistoryItem], k: int = 8) -> str:
    try:
        docs = retrieve(question, k=k)
    except Exception as exc:
        logger.exception("Retrieval failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="The book knowledge base is unavailable. Run python ingest.py first and try again.",
        ) from exc

    context = context_from_documents(docs)
    prompt = build_prompt(question, context, spoiler_mode, history_text(history))
    try:
        return get_llm().generate(prompt)
    except GeminiServiceError as exc:
        raise HTTPException(status_code=503, detail=exc.user_message) from exc
    except Exception as exc:
        logger.exception("Unexpected LLM failure: %s", exc)
        raise HTTPException(status_code=500, detail="The book assistant could not complete that request.") from exc


@app.get("/")
def root():
    return {"message": "Before You Read API is running."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    return {"answer": run_rag(request.question, request.spoiler_mode, request.history)}


@app.post("/recommend")
def recommend(request: RecommendRequest):
    question = (
        "Recommend approximately three books from the retrieved collection for this request. "
        "For each, include title, author, genre, difficulty, pacing, twist level and a short reason. "
        "Do not recommend books that were not retrieved.\nUser request: " + request.query
    )
    return {"answer": run_rag(question, request.spoiler_mode, request.history, k=10)}


@app.post("/recommend/preferences")
def recommend_preferences(request: PreferenceRecommendRequest):
    p = request.preferences
    query = (
        f"Book recommendation preferences. Genres: {', '.join(p.genres) or 'any'}. "
        f"Length: {p.length}. Writing difficulty: {p.difficulty}. "
        f"Desired experience: {', '.join(p.what_you_want) or 'any'}. "
        "Recommend approximately three matching books from the retrieved collection."
    )
    return {"answer": run_rag(query, request.spoiler_mode, [], k=10)}


@app.post("/before-read")
def before_read(request: BeforeReadRequest):
    question = (
        f"Create a 'Before You Read' guide for the book named '{request.book}'. "
        "Include genre, author, approximate length, writing difficulty, reading pace, themes, atmosphere, "
        "emotional intensity, mystery/twist level, reader type, expected reading experience, and things worth paying attention to. "
        "In NO_SPOILERS mode, do not reveal plot resolutions, culprit/killer identity, ending, major twists, or major character reveals."
    )
    return {"answer": run_rag(question, request.spoiler_mode, request.history, k=5)}


@app.post("/compare")
def compare(request: CompareRequest):
    question = (
        f"Compare the two books '{request.book1}' and '{request.book2}'. "
        "Use only retrieved book records. Give a compact comparison of genre, pages, difficulty, pace, twist level, "
        "emotional intensity and themes, then explain which one the user should choose. "
        "If one title cannot be found in the retrieved collection, clearly say so rather than inventing details."
    )
    return {"answer": run_rag(question, request.spoiler_mode, request.history, k=10)}
