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

from app.bank_strategies import BANK_GENERATORS

def create_dummy_csv(filename="test_accounts.csv", rows=None):
    data = []
    valid_bank_codes = list(BANK_GENERATORS.keys())
    # Guarantee at least one valid account per bank
    for bank_code in valid_bank_codes:
        account_number = BANK_GENERATORS[bank_code]()
        data.append({
            "account_number": account_number,
            "bank_code": bank_code,
            "amount": round(fake.pyfloat(left_digits=4, right_digits=2, positive=True, min_value=10, max_value=10000), 2),
            "reference_id": f"TX{fake.random_number(digits=6)}"
        })
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return filename

def test_upload_csv():
    with open("seed_accounts.csv", "rb") as file:
        response = client.post("/upload-csv", files={"file": ("seed_accounts.csv", file, "text/csv")})
    assert response.status_code == 200
    data = response.json()
<<<<<<< HEAD
    assert "files" in data
    from app.bank_strategies import BANK_GENERATORS
    found_valid = False
    for code in BANK_GENERATORS:
        if code in data and "valid" in data[code] and data[code]["valid"] > 0:
            found_valid = True
            break
    assert found_valid, "No valid accounts found in any bank code stats in response"
    os.remove(file_path)
=======
    assert "summary" in data
    assert data["summary"]["total_rows"] == 10000
    assert "columns" in data["summary"]
>>>>>>> 712d468fcd2dfc328a93acfc9751f42a6b479770

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
