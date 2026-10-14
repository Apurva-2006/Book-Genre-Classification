"""FastAPI backend for Book Genre Prediction System using OneVsRest LinearSVC."""
import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import joblib
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

# Configure logging without leaking sensitive payload data
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("book_genre_api")

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = Path(os.getenv("MODEL_DIR", str(BASE_DIR / "models")))
DEFAULT_THRESHOLD = float(os.getenv("DECISION_THRESHOLD", "-0.3"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="Book Genre Prediction API",
    description="Multi-label book genre prediction using TF-IDF and OneVsRest LinearSVC.",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ModelArtifacts:
    """Holds loaded ML model components."""
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.selected_genres: List[str] = []
        self.threshold: float = DEFAULT_THRESHOLD
        self.is_loaded: bool = False
        self.model_type: str = "OneVsRest LinearSVC"

    def load(self, model_dir: Path):
        svm_path = model_dir / "svm_model.joblib"
        vec_path = model_dir / "tfidf_vectorizer.joblib"
        genres_joblib_path = model_dir / "selected_genres.joblib"
        genres_json_path = model_dir / "selected_genres.json"
        bundle_path = model_dir / "genre_model.joblib"

        # Check for separate artifact files first
        has_genres = genres_joblib_path.exists() or genres_json_path.exists()
        if svm_path.exists() and vec_path.exists() and has_genres:
            try:
                self.model = joblib.load(svm_path)
                self.vectorizer = joblib.load(vec_path)

                if genres_joblib_path.exists():
                    self.selected_genres = joblib.load(genres_joblib_path)
                else:
                    with open(genres_json_path, "r", encoding="utf-8") as f:
                        self.selected_genres = json.load(f)

                self.threshold = DEFAULT_THRESHOLD
                self.is_loaded = True
                logger.info("Successfully loaded separate model artifacts from %s (%d genres)", model_dir, len(self.selected_genres))
                return True
            except Exception as exc:
                logger.error("Failed loading separate artifacts: %s", exc)

        # Fallback: check for bundled artifact file
        if bundle_path.exists():
            try:
                bundle = joblib.load(bundle_path)
                self.model = bundle["model"]
                self.vectorizer = bundle["vectorizer"]
                self.selected_genres = bundle["selected_genres"]
                self.threshold = float(bundle.get("threshold", DEFAULT_THRESHOLD))
                self.model_type = bundle.get("model_type", "OneVsRest LinearSVC")
                self.is_loaded = True
                logger.info("Successfully loaded bundled model artifact from %s", bundle_path)
                return True
            except Exception as exc:
                logger.error("Failed loading bundled artifact: %s", exc)

        logger.warning(
            "Model artifacts not found in %s. Please run 'python train_model.py' to generate them.",
            model_dir
        )
        self.is_loaded = False
        return False


artifacts = ModelArtifacts()
# Attempt load at import time so models are immediately available
artifacts.load(MODEL_DIR)


@app.on_event("startup")
def startup_event():
    """Ensure model artifacts are loaded on application startup."""
    if not artifacts.is_loaded:
        artifacts.load(MODEL_DIR)


class BookRequest(BaseModel):
    title: Optional[str] = Field(default="", max_length=300, description="Book title")
    author: Optional[str] = Field(default="", max_length=200, description="Author name")
    description: Optional[str] = Field(default="", max_length=10000, description="Book summary or description")

    # Backwards-compatible aliases from frontend
    book_name: Optional[str] = Field(default=None, max_length=300)
    author_name: Optional[str] = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def populate_and_validate(self):
        # Resolve aliases if primary fields are empty
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


class PredictionResponse(BaseModel):
    success: bool
    input: dict
    genres: List[str]               # Required by Next.js frontend
    predicted_genres: List[str]     # Backward-compatible
    model: str
    threshold: float
    message: Optional[str] = None


@app.get("/")
def root():
    return {
        "service": "Book Genre Prediction API",
        "status": "online",
        "model_loaded": artifacts.is_loaded,
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "documentation": "/docs"
        }
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": artifacts.is_loaded,
        "model_type": artifacts.model_type if artifacts.is_loaded else None,
        "threshold": artifacts.threshold if artifacts.is_loaded else None,
        "genres_count": len(artifacts.selected_genres) if artifacts.is_loaded else 0,
        "selected_genres": artifacts.selected_genres if artifacts.is_loaded else []
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(book: BookRequest):
    if not artifacts.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Model artifacts are not loaded. Please run 'python train_model.py' to train and save "
                "the model artifacts, then reload the API."
            )
        )

    # Combine text in the exact format used during training: title + " " + author + " " + description
    combined_text = f"{book.title} {book.author} {book.description}".strip()
    logger.info("Processing prediction request for title='%s', author='%s'", book.title, book.author)

    try:
        # Transform using existing fitted vectorizer (NEVER fit_transform)
        vector = artifacts.vectorizer.transform([combined_text])

        # Obtain decision scores from OneVsRest LinearSVC using decision_function
        scores = artifacts.model.decision_function(vector)[0]
    except Exception as exc:
        logger.error("Inference failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error during genre prediction: {str(exc)}"
        )

    threshold = artifacts.threshold
    genres = artifacts.selected_genres

    # Identify indices exceeding decision threshold
    matched_indices = [i for i, score in enumerate(scores) if score >= threshold]

    # Sort matching genres by score descending (highest confidence first)
    matched_indices.sort(key=lambda i: scores[i], reverse=True)
    predicted_genres = [genres[i] for i in matched_indices]

    message = None
    if not predicted_genres:
        message = f"No genres exceeded the decision threshold ({threshold})."

    return PredictionResponse(
        success=True,
        input={
            "title": book.title,
            "author": book.author,
        },
        genres=predicted_genres,
        predicted_genres=predicted_genres,
        model=artifacts.model_type,
        threshold=threshold,
        message=message,
    )
