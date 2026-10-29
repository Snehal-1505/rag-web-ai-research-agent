"""
Unit and integration tests for Loomi AI FastAPI server adapter.
"""
import io
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "indexed_documents" in data
    assert "gemini_configured" in data


def test_session_lifecycle():
    # 1. Create session
    create_res = client.post("/api/sessions", json={"title": "Test Research Session"})
    assert create_res.status_code == 201
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Test Research Session"

    # 2. List sessions
    list_res = client.get("/api/sessions")
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert any(s["id"] == session_id for s in sessions)

    # 3. Get session detail
    detail_res = client.get(f"/api/sessions/{session_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == session_id
    assert isinstance(detail["messages"], list)

    # 4. Rename session
    patch_res = client.patch(f"/api/sessions/{session_id}", json={"title": "Renamed Session"})
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Renamed Session"

    # 5. Delete session
    del_res = client.delete(f"/api/sessions/{session_id}")
    assert del_res.status_code == 200

    # 6. Verify deleted
    not_found_res = client.get(f"/api/sessions/{session_id}")
    assert not_found_res.status_code == 404


def test_document_listing_and_upload():
    # 1. List documents
    docs_res = client.get("/api/documents")
    assert docs_res.status_code == 200
    data = docs_res.json()
    assert "documents" in data
    assert "indexed_filenames" in data

    # 2. Test upload with TXT file
    file_content = b"Loomi AI is a next-generation AI research workspace designed with warm editorial aesthetic."
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("loomi_test_doc.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["status"] in ("ready", "duplicate")
    doc_id = upload_data["document_id"]

    # 3. Check document status
    status_res = client.get(f"/api/documents/{doc_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] in ("ready", "duplicate")
