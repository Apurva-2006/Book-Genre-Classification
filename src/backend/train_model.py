"""Train the multi-label book genre classifier from the Goodreads dataset using LinearSVC."""
import ast
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import LinearSVC

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "goodreads_data.csv"
MODEL_DIR = Path(os.getenv("MODEL_DIR", str(BASE_DIR / "models")))
MODEL_DIR.mkdir(parents=True, exist_ok=True)

SELECTED_GENRES = [
    "Fantasy", "Romance", "Mystery", "Thriller", "Historical Fiction",
    "Science Fiction", "Adventure", "Crime", "Horror", "Paranormal",
    "Young Adult", "Biography", "Memoir", "Self Help", "Philosophy",
    "Psychology", "Humor", "Childrens"
]

DEFAULT_DECISION_THRESHOLD = float(os.getenv("DECISION_THRESHOLD", "-0.3"))


def parse_genres(value):
    """Safely parse genres column from stringified list representation."""
    if isinstance(value, list):
        return value
    try:
        parsed = ast.literal_eval(str(value))
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError):
        return []


def combine_features(frame: pd.DataFrame) -> pd.Series:
    """Combine book title, author, and description in standard order."""
    title = frame["Book"].fillna("").astype(str).str.strip()
    author = frame["Author"].fillna("").astype(str).str.strip()
    desc = frame["Description"].fillna("").astype(str).str.strip()
    return (title + " " + author + " " + desc).str.strip()


def create_binary_labels(frame: pd.DataFrame) -> np.ndarray:
    """Generate multi-label binary matrix for selected genres."""
    parsed_genres = frame["Genres"].apply(parse_genres)
    return np.array([[int(g in row) for g in SELECTED_GENRES] for row in parsed_genres])


def train():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Goodreads dataset not found at expected path: {DATA_PATH}")

    print(f"Loading dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    required_cols = {"Book", "Author", "Description", "Genres"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {sorted(missing)}")

    print(f"Dataset loaded. Total rows: {len(df)}")
    texts = combine_features(df)
    labels = create_binary_labels(df)

    # Train / test split for evaluation
    train_texts, test_texts, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )

    print("Evaluating LinearSVC pipeline on validation split...")
    eval_vectorizer = TfidfVectorizer(max_features=10000, stop_words="english")
    X_train_eval = eval_vectorizer.fit_transform(train_texts)
    X_test_eval = eval_vectorizer.transform(test_texts)

    eval_model = OneVsRestClassifier(LinearSVC(random_state=42, max_iter=2000))
    eval_model.fit(X_train_eval, y_train)

    # Evaluate decision scores across candidate thresholds
    decision_scores = eval_model.decision_function(X_test_eval)
    candidate_thresholds = [-0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0.0, 0.1]
    threshold_evals = []

    for thresh in candidate_thresholds:
        preds = (decision_scores >= thresh).astype(int)
        micro = float(f1_score(y_test, preds, average="micro", zero_division=0))
        macro = float(f1_score(y_test, preds, average="macro", zero_division=0))
        all_zero = int((preds.sum(axis=1) == 0).sum())
        threshold_evals.append({
            "threshold": thresh,
            "micro_f1": round(micro, 4),
            "macro_f1": round(macro, 4),
            "zero_prediction_count": all_zero,
        })

    # Evaluate at configured default threshold (-0.3)
    target_preds = (decision_scores >= DEFAULT_DECISION_THRESHOLD).astype(int)
    eval_micro_f1 = float(f1_score(y_test, target_preds, average="micro", zero_division=0))
    eval_macro_f1 = float(f1_score(y_test, target_preds, average="macro", zero_division=0))
    print(f"Evaluation at threshold {DEFAULT_DECISION_THRESHOLD}:")
    print(f"  Micro F1: {eval_micro_f1:.4f} (~{eval_micro_f1 * 100:.2f}%)")
    print(f"  Macro F1: {eval_macro_f1:.4f} (~{eval_macro_f1 * 100:.2f}%)")

    # Fit final production model on the complete dataset
    print("\nFitting final production TF-IDF vectorizer and OneVsRest LinearSVC on full dataset...")
    final_vectorizer = TfidfVectorizer(max_features=10000, stop_words="english")
    X_full = final_vectorizer.fit_transform(texts)

    final_model = OneVsRestClassifier(LinearSVC(random_state=42, max_iter=2000))
    final_model.fit(X_full, labels)

    # Save artifacts: both individual files and bundled fallback
    svm_path = MODEL_DIR / "svm_model.joblib"
    vec_path = MODEL_DIR / "tfidf_vectorizer.joblib"
    genres_path = MODEL_DIR / "selected_genres.joblib"
    genres_json_path = MODEL_DIR / "selected_genres.json"
    bundle_path = MODEL_DIR / "genre_model.joblib"
    report_path = MODEL_DIR / "training_report.json"

    print(f"Saving artifacts to {MODEL_DIR}...")
    joblib.dump(final_model, svm_path)
    joblib.dump(final_vectorizer, vec_path)
    joblib.dump(SELECTED_GENRES, genres_path)
    genres_json_path.write_text(json.dumps(SELECTED_GENRES, indent=2), encoding="utf-8")

    # Bundled artifact for easy single-file deployment
    joblib.dump({
        "model": final_model,
        "vectorizer": final_vectorizer,
        "selected_genres": SELECTED_GENRES,
        "threshold": DEFAULT_DECISION_THRESHOLD,
        "model_type": "OneVsRest LinearSVC",
    }, bundle_path)

    report = {
        "model_type": "OneVsRest LinearSVC",
        "dataset_rows": int(len(df)),
        "num_genres": len(SELECTED_GENRES),
        "selected_genres": SELECTED_GENRES,
        "default_decision_threshold": DEFAULT_DECISION_THRESHOLD,
        "eval_metrics_at_default_threshold": {
            "micro_f1": round(eval_micro_f1, 4),
            "macro_f1": round(eval_macro_f1, 4),
        },
        "threshold_evaluations": threshold_evals,
        "note": (
            "Threshold evaluated on a 20% test split. Final model refit on all dataset rows. "
            "LinearSVC uses decision_function scores, NOT probability scores."
        )
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nTraining complete!")
    print(f" - Saved SVM Model:          {svm_path}")
    print(f" - Saved TF-IDF Vectorizer:  {vec_path}")
    print(f" - Saved Genre List:         {genres_path}")
    print(f" - Saved Bundled Model:      {bundle_path}")
    print(f" - Saved Training Report:    {report_path}")


if __name__ == "__main__":
    train()
