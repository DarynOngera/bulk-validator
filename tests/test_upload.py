# tests/test_upload.py

import pytest
from fastapi.testclient import TestClient
from faker import Faker
import pandas as pd
import os
from app.main import app

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
    file_path = create_dummy_csv()
    with open(file_path, "rb") as f:
        response = client.post("/upload-csv", files={"file": (file_path, f, "text/csv")})

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "valid_accounts" in data
    assert "invalid_accounts" in data
    os.remove(file_path)

def test_download_report():
    response = client.get("/download-report")
    if response.status_code == 200:
        assert response.headers["content-type"] == "text/csv"
    else:
        assert response.status_code == 404
