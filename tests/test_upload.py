# tests/test_upload.py

import pytest
from fastapi.testclient import TestClient
from faker import Faker
import pandas as pd
import os
from app.main import app

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
    file_path = create_dummy_csv()
    with open(file_path, "rb") as f:
        response = client.post("/upload-csv", files={"file": (file_path, f, "text/csv")})

    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    from app.bank_strategies import BANK_GENERATORS
    found_valid = False
    for code in BANK_GENERATORS:
        if code in data and "valid" in data[code] and data[code]["valid"] > 0:
            found_valid = True
            break
    assert found_valid, "No valid accounts found in any bank code stats in response"
    os.remove(file_path)

def test_download_report():
    response = client.get("/download-report")
    if response.status_code == 200:
        assert response.headers["content-type"] == "text/csv"
    else:
        assert response.status_code == 404
