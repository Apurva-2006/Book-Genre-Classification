"""Automated test suite for Book Genre Prediction API using standard unittest and TestClient."""
import unittest
import numpy as np
from fastapi.testclient import TestClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import LinearSVC

from main import app, artifacts, BookRequest, DEFAULT_THRESHOLD

SAMPLE_GENRES = [
    "Fantasy", "Romance", "Mystery", "Thriller", "Historical Fiction",
    "Science Fiction", "Adventure", "Crime", "Horror", "Paranormal",
    "Young Adult", "Biography", "Memoir", "Self Help", "Philosophy",
    "Psychology", "Humor", "Childrens"
]


class TestBookGenreBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_root_endpoint(self):
        """Verify root endpoint returns API information."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("/predict", data["endpoints"]["predict"])

    def test_02_health_endpoint(self):
        """Verify health endpoint returns status and model availability."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIsInstance(data["model_loaded"], bool)

    def test_03_predict_without_model_returns_503(self):
        """Verify 503 Service Unavailable when model artifacts are not loaded."""
        saved_loaded = artifacts.is_loaded
        artifacts.is_loaded = False
        try:
            response = self.client.post("/predict", json={
                "title": "Dune",
                "author": "Frank Herbert",
                "description": "A science fiction epic on the desert planet Arrakis."
            })
            self.assertEqual(response.status_code, 503)
            self.assertIn("train_model.py", response.json()["detail"])
        finally:
            artifacts.is_loaded = saved_loaded

    def test_04_input_validation_empty_payload(self):
        """Verify 422 Unprocessable Entity when all fields are empty or whitespace."""
        response = self.client.post("/predict", json={})
        self.assertEqual(response.status_code, 422)

        response = self.client.post("/predict", json={
            "title": "   ",
            "author": "",
            "description": "  "
        })
        self.assertEqual(response.status_code, 422)

    def test_05_input_validation_partial_fields_and_aliases(self):
        """Verify request accepts partial fields and backward-compatible aliases."""
        req = BookRequest(title="Some Book Title")
        self.assertEqual(req.title, "Some Book Title")
        self.assertEqual(req.author, "")
        self.assertEqual(req.description, "")

        # Aliases test
        req_alias = BookRequest(book_name="Alias Title", author_name="Alias Author")
        self.assertEqual(req_alias.title, "Alias Title")
        self.assertEqual(req_alias.author, "Alias Author")

    def test_06_prediction_pipeline_with_linearsvc(self):
        """Verify prediction logic, decision_function scoring, thresholding, and output format."""
        # Fit a small synthetic OneVsRest LinearSVC for deterministic pipeline validation
        corpus = [
            "Harry Potter wizard magic adventure fantasy hogwarts",
            "Sherlock Holmes detective mystery crime investigation clue",
            "Galactic empire spaceship stars science fiction aliens",
            "Love affair dating marriage romance emotions heart",
        ]
        labels = np.zeros((4, len(SAMPLE_GENRES)), dtype=int)
        labels[0, SAMPLE_GENRES.index("Fantasy")] = 1
        labels[0, SAMPLE_GENRES.index("Adventure")] = 1
        labels[1, SAMPLE_GENRES.index("Mystery")] = 1
        labels[1, SAMPLE_GENRES.index("Crime")] = 1
        labels[2, SAMPLE_GENRES.index("Science Fiction")] = 1
        labels[3, SAMPLE_GENRES.index("Romance")] = 1

        vec = TfidfVectorizer(max_features=10000, stop_words="english")
        X = vec.fit_transform(corpus)
        svm = OneVsRestClassifier(LinearSVC(random_state=42, max_iter=1000))
        svm.fit(X, labels)

        # Inject into artifacts
        saved_loaded = artifacts.is_loaded
        saved_model = artifacts.model
        saved_vec = artifacts.vectorizer
        saved_genres = artifacts.selected_genres
        saved_threshold = artifacts.threshold

        try:
            artifacts.model = svm
            artifacts.vectorizer = vec
            artifacts.selected_genres = SAMPLE_GENRES
            artifacts.threshold = -0.3
            artifacts.is_loaded = True

            # 1. Normal prediction matching genres
            response = self.client.post("/predict", json={
                "title": "Harry Potter and the Chamber of Secrets",
                "author": "J.K. Rowling",
                "description": "Wizard magic adventure fantasy school"
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertTrue(data["success"])
            self.assertEqual(data["model"], "OneVsRest LinearSVC")
            self.assertEqual(data["input"]["title"], "Harry Potter and the Chamber of Secrets")
            self.assertEqual(data["input"]["author"], "J.K. Rowling")
            self.assertIsInstance(data["predicted_genres"], list)
            self.assertIn("genres", data)
            self.assertEqual(data["genres"], data["predicted_genres"])
            # Ensure multi-label prediction occurred and matched expected genres
            self.assertTrue(any(g in data["predicted_genres"] for g in ["Fantasy", "Adventure"]))

            # 2. Case where no genre passes high threshold: must return empty list without fabricating genres
            artifacts.threshold = 999.0
            response_empty = self.client.post("/predict", json={
                "title": "Unknown Title",
                "author": "Anonymous",
                "description": "Gibberish unrelated terms xyz"
            })
            self.assertEqual(response_empty.status_code, 200)
            data_empty = response_empty.json()
            self.assertEqual(data_empty["predicted_genres"], [])
            self.assertIsNotNone(data_empty["message"])
            self.assertIn("No genres exceeded the decision threshold", data_empty["message"])

        finally:
            artifacts.is_loaded = saved_loaded
            artifacts.model = saved_model
            artifacts.vectorizer = saved_vec
            artifacts.selected_genres = saved_genres
            artifacts.threshold = saved_threshold

    def test_07_cors_headers(self):
        """Verify CORS preflight returns access-control headers."""
        response = self.client.options("/predict", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("access-control-allow-origin", response.headers)


class TestModelsStandaloneApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from models.app import app as models_app
        cls.client = TestClient(models_app)

    def test_01_models_app_endpoints(self):
        """Verify models/app.py root, health, predict, and CORS."""
        root_res = self.client.get("/")
        self.assertEqual(root_res.status_code, 200)

        health_res = self.client.get("/health")
        self.assertEqual(health_res.status_code, 200)
        self.assertTrue(health_res.json()["model_loaded"])

        predict_res = self.client.post("/predict", json={
            "book_name": "The Hobbit",
            "author_name": "J.R.R. Tolkien",
            "description": "A fantasy journey with wizards and hobbits to the lonely mountain."
        })
        self.assertEqual(predict_res.status_code, 200)
        data = predict_res.json()
        self.assertTrue(data["success"])
        self.assertIn("genres", data)
        self.assertIn("Fantasy", data["genres"])

        cors_res = self.client.options("/predict", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        })
        self.assertEqual(cors_res.status_code, 200)
        self.assertIn("access-control-allow-origin", cors_res.headers)


if __name__ == "__main__":
    unittest.main()

