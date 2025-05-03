# tests/test_upload.py

import pytest
from fastapi.testclient import TestClient
from faker import Faker
import pandas as pd
import os
from app.main import app
from app.email_notify import send_validation_report_email

client = TestClient(app)
fake = Faker()

def create_dummy_csv(filename="test_accounts.csv", rows=5):
    data = []
    for _ in range(rows):
        data.append({
            "account": fake.random_number(digits=4),
            "name": fake.name(),
            "email": fake.email(),
            "account_number": fake.random_number(digits=10),
            "bank_code": fake.random_number(digits=3)
        })
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return filename

def test_upload_csv():
    with open("seed_accounts.csv", "rb") as file:
        response = client.post("/upload-csv", files={"file": ("seed_accounts.csv", file, "text/csv")})
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["summary"]["total_rows"] == 10000
    assert "columns" in data["summary"]

def test_download_report():
    response = client.get("/download-report")
    if response.status_code == 200:
        assert response.headers["content-type"] == "text/csv"
    else:
        assert response.status_code == 404

@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """
    Send email notification after the test session finishes.
    """
    recipient = os.getenv("TEST_NOTIFY_EMAIL", "your_email@example.com")
    subject = "Test Results Notification"
    body = f"Test session completed with exit status: {exitstatus}.\n"
    body += f"Total tests: {session.testscollected}\n"
    body += f"Passed: {len(session.stats.get('passed', []))}\n"
    body += f"Failed: {len(session.stats.get('failed', []))}\n"
    body += f"Skipped: {len(session.stats.get('skipped', []))}\n"

    try:
        send_validation_report_email(
            recipient=recipient,
            subject=subject,
            body=body
        )
        print(f"Test results email sent to {recipient}.")
    except Exception as e:
        print(f"Failed to send test results email: {e}")
