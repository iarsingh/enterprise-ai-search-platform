from fastapi.testclient import TestClient
from entsearch.main import app

client = TestClient(app)


def test_answers_and_refuses():
    hit = client.post("/ask", json={"question": 'When are invoices paid on net 45?'}).json()
    assert hit["answered"] is True
    assert hit["citation"] == "fin"
    miss = client.post("/ask", json={"question": 'lyrics'}).json()
    assert miss["answered"] is False


def test_empty_is_refused():
    assert client.post("/ask", json={"question": " "}).status_code == 422
