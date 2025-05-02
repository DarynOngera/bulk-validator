# app/validator.py

def validate_account_row(row):
    acct = str(row["account_number"]).strip()
    bank_code = str(row["bank_code"]).strip()

    if not acct.isdigit() or len(acct) < 10:
        return {
            "valid": False,
            "data": {
                "account_number": acct,
                "bank_code": bank_code,
                "reason": "Invalid format (must be 10+ digits)"
            }
        }

    # Simulate random rejection (mock)
    if acct.endswith("0"):
        return {
            "valid": False,
            "data": {
                "account_number": acct,
                "bank_code": bank_code,
                "reason": "Account does not exist (simulated)"
            }
        }

    return {
        "valid": True,
        "data": {
            "account_number": acct,
            "bank_code": bank_code,
            "status": "Valid"
        }
    }
