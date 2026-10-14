# Book Genre Prediction System — Backend

FastAPI backend for multi-label book genre prediction using **TF-IDF** feature extraction and **OneVsRest LinearSVC**.

Given a book's **title**, **author**, and **description**, the system predicts multiple relevant genres from 18 selected categories using an SVM decision score threshold.

---

## 1. Machine Learning Pipeline Overview

- **Dataset**: `data/goodreads_data.csv` (~11,000 titles).
- **Genres (18 categories)**:
  - `Fantasy`, `Romance`, `Mystery`, `Thriller`, `Historical Fiction`, `Science Fiction`, `Adventure`, `Crime`, `Horror`, `Paranormal`, `Young Adult`, `Biography`, `Memoir`, `Self Help`, `Philosophy`, `Psychology`, `Humor`, `Childrens`
- **Text Preprocessing**: Combines fields in fixed order: `title + " " + author + " " + description`.
- **Vectorization**: `TfidfVectorizer(max_features=10000, stop_words="english")`.
- **Classifier**: `OneVsRestClassifier(LinearSVC(max_iter=2000))`.
- **Inference Scoring**: Uses SVM `decision_function()` scores (NOT probabilities).
- **Default Decision Threshold**: `-0.3` (configurable via `DECISION_THRESHOLD` environment variable).

---

## 2. Project Structure

```
audiobook_backend/
├── data/
│   └── goodreads_data.csv          # Goodreads book dataset
├── models/                         # Saved artifacts (generated after training)
│   ├── svm_model.joblib            # Trained OneVsRest LinearSVC model
│   ├── tfidf_vectorizer.joblib     # Fitted TF-IDF vectorizer
│   ├── selected_genres.joblib      # Ordered genre labels (joblib format)
│   ├── selected_genres.json        # Ordered genre labels (JSON format)
│   ├── genre_model.joblib          # Bundled fallback artifact
│   └── training_report.json        # Evaluation metrics & threshold report
├── main.py                         # FastAPI application & endpoints
├── train_model.py                  # Model training and artifact export script
├── test_backend.py                 # Automated test suite (unittest / pytest)
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

---

## 3. Setup & Installation

### Step 1: Create Virtual Environment & Install Dependencies

```bash
# In the audiobook_backend directory:
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate

# Install required packages:
pip install -r requirements.txt
```

### Step 2: Train Model Artifacts

Run the training script to evaluate the pipeline and save the trained model artifacts into `models/`:

```bash
python train_model.py
```

This generates:
- `models/svm_model.joblib`
- `models/tfidf_vectorizer.joblib`
- `models/selected_genres.joblib`
- `models/genre_model.joblib` (bundled fallback)
- `models/training_report.json`

### Step 3: Run Automated Tests

Verify backend behavior, validation, and pipeline mechanics:

```bash
python test_backend.py
```

---

## 4. Running the API

Start the Uvicorn development server:

```bash
uvicorn main:app --reload --port 8000
```

- **Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Docs (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 5. API Endpoints

### `GET /health`
Returns server status and whether model artifacts are loaded.

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_type": "OneVsRest LinearSVC",
  "threshold": -0.3,
  "genres_count": 18,
  "selected_genres": [
    "Fantasy", "Romance", "Mystery", "Thriller", "Historical Fiction",
    "Science Fiction", "Adventure", "Crime", "Horror", "Paranormal",
    "Young Adult", "Biography", "Memoir", "Self Help", "Philosophy",
    "Psychology", "Humor", "Childrens"
  ]
}
```

### `POST /predict`
Predicts multiple genres based on title, author, and description.

**Request JSON:**
```json
{
  "title": "Harry Potter and the Philosopher's Stone",
  "author": "J.K. Rowling",
  "description": "Harry Potter thinks he is an ordinary boy until he is rescued by an owl and learns to play Quidditch."
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "input": {
    "title": "Harry Potter and the Philosopher's Stone",
    "author": "J.K. Rowling"
  },
  "predicted_genres": [
    "Fantasy",
    "Young Adult",
    "Childrens"
  ],
  "model": "OneVsRest LinearSVC",
  "threshold": -0.3,
  "message": null
}
```

**Below-Threshold Response (200 OK):**
If no genre exceeds the `-0.3` threshold, an empty list is returned without inventing a genre:
```json
{
  "success": true,
  "input": {
    "title": "Some Unknown Book",
    "author": "Unknown Author"
  },
  "predicted_genres": [],
  "model": "OneVsRest LinearSVC",
  "threshold": -0.3,
  "message": "No genres exceeded the decision threshold (-0.3)."
}
```

**Missing Model Response (503 Service Unavailable):**
If the server starts before running `train_model.py`:
```json
{
  "detail": "Model artifacts are not loaded. Please run 'python train_model.py' to train and save the model artifacts, then reload the API."
}
```

---

## 6. Frontend Integration Guide

A frontend (Streamlit, React, Vue, or vanilla HTML/JS) can connect to `http://127.0.0.1:8000/predict`.

### Example Frontend Request (JavaScript / Fetch)

```javascript
async function predictGenres(title, author, description) {
  try {
    const response = await fetch("http://127.0.0.1:8000/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: title,
        author: author,
        description: description,
      }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Prediction request failed.");
    }

    const data = await response.json();
    return data.predicted_genres; // Array of strings, e.g. ["Fantasy", "Young Adult"]
  } catch (error) {
    console.error("Error predicting genres:", error);
    throw error;
  }
}
```

---

## 7. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DECISION_THRESHOLD` | `-0.3` | SVM decision score cutoff for genre inclusion |
| `MODEL_DIR` | `<project>/models` | Directory containing joblib model artifacts |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS allowed origins |
