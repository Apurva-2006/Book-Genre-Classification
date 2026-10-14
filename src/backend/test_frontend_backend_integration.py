"""End-to-End integration test simulating the exact Next.js frontend calls to the FastAPI backend."""
import json
import urllib.request
import urllib.error
import subprocess
import time
import sys

def run_integration_test():
    print("Testing backend and frontend endpoint connection...")
    
    # 1. Test using FastAPI TestClient directly first
    from fastapi.testclient import TestClient
    from main import app, artifacts
    
    client = TestClient(app)
    
    print(f"Backend model loaded: {artifacts.is_loaded} ({len(artifacts.selected_genres)} genres)")
    
    # Check GET /
    res_root = client.get("/")
    assert res_root.status_code == 200, f"Root returned {res_root.status_code}"
    print("[PASS] GET / -> 200 OK")
    
    # Check GET /health
    res_health = client.get("/health")
    assert res_health.status_code == 200, f"Health returned {res_health.status_code}"
    health_data = res_health.json()
    assert health_data["status"] == "ok"
    assert health_data["model_loaded"] is True
    print(f"[PASS] GET /health -> status: ok, model_loaded: True, genres: {health_data['genres_count']}")
    
    # Check CORS headers (Options preflight as sent by browser fetch)
    res_options = client.options("/predict", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    })
    assert res_options.status_code == 200
    assert "access-control-allow-origin" in res_options.headers
    print(f"[PASS] OPTIONS /predict (CORS preflight) -> allowed origin: {res_options.headers.get('access-control-allow-origin')}")
    
    # Check POST /predict with exact Frontend payload structure:
    # { book_name, author_name, description }
    frontend_payload = {
        "book_name": "The Hobbit",
        "author_name": "J.R.R. Tolkien",
        "description": "Bilbo Baggins, a hobbit enjoying his peaceful life, is swept into an epic quest by Gandalf the wizard and thirteen dwarves to reclaim the Lonely Mountain and treasure guarded by Smaug the dragon."
    }
    
    res_predict = client.post("/predict", json=frontend_payload, headers={
        "Origin": "http://localhost:3000"
    })
    assert res_predict.status_code == 200, f"Predict failed: {res_predict.text}"
    predict_data = res_predict.json()
    
    # Verify response schema matches classifyBook.ts normalise expectations:
    # expects data.genres to be an Array of strings or { label, confidence } objects
    assert "genres" in predict_data, "Response missing 'genres' key required by frontend"
    assert isinstance(predict_data["genres"], list), "'genres' must be a list"
    assert len(predict_data["genres"]) > 0, "Expected at least 1 predicted genre"
    
    print(f"[PASS] POST /predict with Next.js payload -> returned genres: {predict_data['genres']}")
    
    # Test second example (Thriller / Mystery)
    mystery_payload = {
        "book_name": "The Girl with the Dragon Tattoo",
        "author_name": "Stieg Larsson",
        "description": "A financial journalist and a tattooed punk hacker investigate the disappearance of an heiress from a wealthy Swedish industrial family decades earlier, uncovering dark secrets."
    }
    res_mystery = client.post("/predict", json=mystery_payload)
    assert res_mystery.status_code == 200
    print(f"[PASS] POST /predict (Mystery/Thriller) -> returned genres: {res_mystery.json()['genres']}")
    
    print("\nALL FRONTEND-BACKEND ENDPOINT INTEGRATION TESTS PASSED!")

if __name__ == "__main__":
    run_integration_test()
