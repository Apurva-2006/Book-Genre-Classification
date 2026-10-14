"""FastAPI standalone service for Book Genre Prediction API."""
import json
import logging
from pathlib import Path
from typing import List, Optional

import joblib
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("models_app")

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Book Genre Prediction API",
    description="Multi-label book genre prediction using TF-IDF and OneVsRest LinearSVC.",
    version="1.1.0",
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load saved artifacts relative to this file
svm_path = BASE_DIR / "svm_model.joblib"
tfidf_path = BASE_DIR / "tfidf_vectorizer.joblib"
genres_json_path = BASE_DIR / "selected_genres.json"
genres_joblib_path = BASE_DIR / "selected_genres.joblib"

svm_model = None
tfidf = None
selected_genres: List[str] = []
model_loaded = False

try:
    if svm_path.exists() and tfidf_path.exists():
        svm_model = joblib.load(svm_path)
        tfidf = joblib.load(tfidf_path)

        if genres_json_path.exists():
            with open(genres_json_path, "r", encoding="utf-8") as f:
                selected_genres = json.load(f)
        elif genres_joblib_path.exists():
            selected_genres = joblib.load(genres_joblib_path)

        model_loaded = True
        logger.info("Successfully loaded model artifacts (genres: %d)", len(selected_genres))
    else:
        logger.warning("Model artifact files not found in %s", BASE_DIR)
except Exception as err:
    logger.error("Failed loading model artifacts: %s", err)

THRESHOLD = -0.35


class BookInput(BaseModel):
    title: Optional[str] = Field(default="", max_length=300, description="Book title")
    author: Optional[str] = Field(default="", max_length=200, description="Author name")
    description: Optional[str] = Field(default="", max_length=10000, description="Book summary")

    # Frontend aliases
    book_name: Optional[str] = Field(default=None, max_length=300)
    author_name: Optional[str] = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def populate_and_validate(self):
        if not (self.title and self.title.strip()) and (self.book_name and self.book_name.strip()):
            self.title = self.book_name
        if not (self.author and self.author.strip()) and (self.author_name and self.author_name.strip()):
            self.author = self.author_name

        self.title = (self.title or "").strip()
        self.author = (self.author or "").strip()
        self.description = (self.description or "").strip()

        if not any([self.title, self.author, self.description]):
            raise ValueError("At least one field (title, author, or description) must be provided.")
        return self


@app.get("/")
def home():
    return {
        "message": "Book Genre Prediction API is running",
        "status": "online",
        "model_loaded": model_loaded,
        "genres_count": len(selected_genres)
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "threshold": THRESHOLD,
        "genres_count": len(selected_genres),
        "selected_genres": selected_genres
    }


@app.post("/predict")
def predict(book: BookInput):
    if not model_loaded or svm_model is None or tfidf is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model artifacts are not loaded. Please ensure model files are present."
        )

    text = f"{book.title} {book.author} {book.description}".strip()

    X_new = tfidf.transform([text])
    scores = svm_model.decision_function(X_new)[0]

    # Filter and sort by score descending (highest confidence first)
    matched = [i for i, score in enumerate(scores) if score >= THRESHOLD]
    matched.sort(key=lambda i: scores[i], reverse=True)
    genres = [selected_genres[i] for i in matched]

    return {
        "success": True,
        "book": book.title,
        "genres": genres,              # Format expected by Next.js frontend
        "predicted_genres": genres,     # Backward compatibility
        "threshold": THRESHOLD
    }
