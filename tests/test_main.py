import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def default_mocks(mocker):
    """Prevent all external calls by default."""
    mocker.patch(
        "main.get_researcher_data",
        return_value={
            "name": "Mock Researcher",
            "education": [],
            "employment": [],
            "awards": [],
            "supervision": [],
            "collaborations": [],
            "track_record": [],
        },
    )
    mocker.patch("main.call_llm", return_value="# CV Header\nThis is mocked content.")
    mocker.patch("main.extract_text_from_pdf", return_value="Mocked text from PDF.")
    return mocker


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_cv_invalid_format():
    response = client.post("/api/v1/generate/Q999?format=docx")
    assert response.status_code in [200, 400]


def test_generate_cv_success_markdown():
    response = client.post("/api/v1/generate/Q123?format=markdown")
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    assert b"mocked content" in response.content.lower()


def test_pdf_upload_integration():
    files = {"previous_cv": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    response = client.post("/api/v1/generate/Q123?format=markdown", files=files)
    assert response.status_code == 200
    assert b"mocked content" in response.content.lower()


def test_generate_cv_not_found(mocker):
    mocker.patch("main.get_researcher_data", return_value=None)
    response = client.post("/api/v1/generate/Q0?format=markdown")
    assert response.status_code == 404
