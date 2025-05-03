import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOCARDLESS_API_URL = os.getenv("GOCARDLESS_API_URL", "https://bankaccountdata.gocardless.com/api/v2")
SECRET_ID = os.getenv("GOCARDLESS_SECRET_ID")
SECRET_KEY = os.getenv("GOCARDLESS_SECRET_KEY")

class GoCardlessClient:
    def __init__(self):
        self.access_token = None
        self.token_expiry = 0

    def authenticate(self):
        url = f"{GOCARDLESS_API_URL}/token/new/"
        payload = {"secret_id": SECRET_ID, "secret_key": SECRET_KEY}
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data["access"]
            self.token_expiry = data["access_expires"]
        else:
            raise Exception(f"GoCardless Auth failed: {resp.text}")

    def get_institutions(self, country="gb"):
        if not self.access_token:
            self.authenticate()
        url = f"{GOCARDLESS_API_URL}/institutions/?country={country}"
        headers = {"Authorization": f"Bearer {self.access_token}", "accept": "application/json"}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"GoCardless institution fetch failed: {resp.text}")

    def is_valid_bank_code(self, bank_code, country="gb"):
        institutions = self.get_institutions(country)
        for inst in institutions:
            if inst.get("bic") == bank_code or inst.get("id") == bank_code:
                return True
        return False
