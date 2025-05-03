from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles
from app.validators.account_validator import AccountValidator

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class AccountData(BaseModel):
    account_number: str
    bank_code: str
    amount: float
    reference_id: str

import json
from fastapi import Body

@app.post("/validate")
async def validate_account_endpoint(account: AccountData):
    validator = AccountValidator()
    result = await validator.validate(account.dict())
    return result

class TransferData(BaseModel):
    account_number: str
    bank_code: str
    amount: float
    reference_id: str
    recipient_name: str

@app.post("/transfer")
async def transfer_funds(data: TransferData = Body(...)):
    # First layer: check valid_accounts.json
    try:
        with open("app/valid_accounts.json") as f:
            valid_accounts = json.load(f)
        found = any(
            acc["account_number"] == data.account_number and acc["bank_code"] == data.bank_code
            for acc in valid_accounts
        )
        if found:
            return {"status": "success", "message": f"Transfer simulated: {data.amount} to {data.recipient_name} ({data.account_number}) [found in valid_accounts.json]"}
    except Exception:
        pass
    # Second layer: use validation logic
    validator = AccountValidator()
    result = await validator.validate({
        "account_number": data.account_number,
        "bank_code": data.bank_code,
        "amount": data.amount,
        "reference_id": data.reference_id
    })
    if result.get("status") == "Valid":
        return {"status": "success", "message": f"Transfer simulated: {data.amount} to {data.recipient_name} ({data.account_number}) [validated]"}
    else:
        return {"status": "failed", "errors": result.get("errors", [])}

@app.get("/")
def root():
    return {"message": "Bulk Validator Real-Time API", "endpoints": ["/validate"]}

@app.get("/health")
def health():
    return {"status": "ok"}
