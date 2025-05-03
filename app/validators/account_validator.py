# app/validators/account_validator.py

import re
<<<<<<< HEAD
from typing import Dict
from app.bank_strategies import BANK_VALIDATORS
=======
import random
from typing import Dict, List

# SEPA error codes
SEPA_ERROR_CODES = {
    "AC01": "Incorrect account number/IBAN format",
    "AC04": "Closed account number",
    "AC06": "Blocked account",
    "AM09": "Invalid amount",
    "BE04": "Invalid bank code",
    "RR01": "Regulatory restriction",
    "RF01": "Invalid reference ID"
}
>>>>>>> 712d468fcd2dfc328a93acfc9751f42a6b479770

class AccountValidator:
    def __init__(self):
        # Realistic bank codes
        self.valid_bank_codes = ["001", "002", "003", "044", "058", "070", "232", "082", "214", "215"]
        self.validation_rules = [
            {
                "name": "iban_format_or_checksum",
                "rule": lambda x: self._looks_like_iban(x) and not self._validate_iban(x),
                "message": SEPA_ERROR_CODES["AC01"],
                "code": "AC01"
            },
            {
                "name": "length_error",
                "rule": lambda x: not self._looks_like_iban(x) and not (8 <= len(x) <= 12),
                "message": SEPA_ERROR_CODES["AC01"],
                "code": "AC01"
            },
            {
                "name": "alphanumeric_format",
                "rule": lambda x: not self._looks_like_iban(x) and not x.isalnum(),
                "message": SEPA_ERROR_CODES["AC01"],
                "code": "AC01"
            },
            {
                "name": "bank_code_validation",
                "rule": lambda x, bank_code: not self._looks_like_iban(x) and bank_code not in self.valid_bank_codes,
                "message": SEPA_ERROR_CODES["BE04"],
                "code": "BE04"
            },
            {
                "name": "luhn_checksum",
                "rule": lambda x: not self._looks_like_iban(x) and (x.isdigit() and len(x) == 10 and not self._validate_checksum(x)),
                "message": SEPA_ERROR_CODES["AC01"],
                "code": "AC01"
            },
            {
                "name": "amount_validation",
                "rule": lambda x, amount: not self._validate_amount(amount),
                "message": SEPA_ERROR_CODES["AM09"],
                "code": "AM09"
            },
            {
                "name": "reference_id_validation",
                "rule": lambda x, amount, reference_id: not reference_id,
                "message": SEPA_ERROR_CODES["RF01"],
                "code": "RF01"
            }
        ]

    def _looks_like_iban(self, account: str) -> bool:
        # IBAN: 2 letters (country), 2 digits (check), rest alphanumeric, length 15-34
        return bool(re.match(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$", account.upper()))

    def _validate_iban(self, iban: str) -> bool:
        # Remove spaces and uppercase
        iban = iban.replace(' ', '').upper()
        # Basic format check
        if not re.match(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$", iban):
            return False
        # Country-specific length check (optional, here just 15-34)
        if not (15 <= len(iban) <= 34):
            return False
        # Rearrange
        rearranged = iban[4:] + iban[:4]
        # Convert letters to numbers (A=10, B=11, ..., Z=35)
        numerized = ''
        for c in rearranged:
            if c.isdigit():
                numerized += c
            else:
                numerized += str(ord(c) - 55)
        # MOD-97
        try:
            return int(numerized) % 97 == 1
        except Exception:
            return False

    def _validate_bank_code(self, bank_code: str) -> bool:
        """Validate bank code format and existence"""
        return bank_code in self.valid_bank_codes

    def _validate_checksum(self, account: str) -> bool:
        """Validate account number checksum using Luhn algorithm"""
        try:
            # Only validate checksum for numeric accounts
            if not account.isdigit():
                return False
            
            digits = [int(d) for d in account]
            sum_ = sum(digits[-1::-2]) + sum(sum(divmod(d*2,10)) for d in digits[-2::-2])
            return sum_ % 10 == 0
        except ValueError:
            return False

    def _validate_amount(self, amount: float) -> bool:
        """Validate transaction amount"""
        return amount > 0 and amount <= 10000000  # Max 10M limit

    async def mock_bank_api_check(self, account: str, bank_code: str) -> Dict:
        """Simulates real bank API checks with probabilistic errors"""
        # 5% chance of closed account
        if random.random() < 0.05:  
            return {"valid": False, "code": "AC04", "message": SEPA_ERROR_CODES["AC04"]}
        # 2% chance regulatory block
        elif account.startswith("X") and random.random() < 0.02:
            return {"valid": False, "code": "RR01", "message": SEPA_ERROR_CODES["RR01"]}
        # 3% chance blocked account
        elif account.endswith("000") and random.random() < 0.03:
            return {"valid": False, "code": "AC06", "message": SEPA_ERROR_CODES["AC06"]}
        return {"valid": True}

    async def validate(self, account_data: Dict) -> Dict:
        """
        Validate account details
        
        Args:
            account_data: Dictionary containing account details
                - account_number: str
                - bank_code: str
                - amount: float
                - reference_id: str
                
        Returns:
            Dict with validation results
        """
        account = account_data.get('account_number', '').strip()
        bank_code = account_data.get('bank_code', '')
        amount = account_data.get('amount', 0)
        reference_id = account_data.get('reference_id', '')
        
        # Basic validation
        if not account or not bank_code or amount is None or reference_id is None:
            return {
                "status": "Invalid",
                "errors": [
                    {
                        "type": "format_error",
                        "message": "Missing required fields"
                    }
                ]
            }

        # --- Per-bank custom validation ---
        if bank_code in BANK_VALIDATORS:
            is_valid = BANK_VALIDATORS[bank_code](account)
            if not is_valid:
                return {
                    "status": "Invalid",
                    "errors": [{
                        "type": f"bank_{bank_code}_account_validation",
                        "message": f"Account number failed validation for bank {bank_code}"
                    }],
                    "account_number": account,
                    "bank_code": bank_code,
                    "amount": amount,
                    "reference_id": reference_id
                }
            # If valid, continue to other rules (amount, reference)

        # Detailed validation
        validation_errors = []
        for rule in self.validation_rules:
            # Each rule may require different args
            if rule["name"] == "bank_code_validation":
                if rule["rule"](account, bank_code):
                    validation_errors.append({
                        "type": rule["name"],
                        "code": rule["code"],
                        "message": rule["message"]
                    })
            elif rule["name"] == "amount_validation":
                if rule["rule"](account, amount):
                    validation_errors.append({
                        "type": rule["name"],
                        "code": rule["code"],
                        "message": rule["message"]
                    })
            elif rule["name"] == "reference_id_validation":
                if rule["rule"](account, amount, reference_id):
                    validation_errors.append({
                        "type": rule["name"],
                        "code": rule["code"],
                        "message": rule["message"]
                    })
            else:
                if rule["rule"](account):
                    validation_errors.append({
                        "type": rule["name"],
                        "code": rule["code"],
                        "message": rule["message"]
                    })

        # Simulate bank API checks for existing accounts
        if not validation_errors:  # Only check if format is valid
            bank_api_result = await self.mock_bank_api_check(account, bank_code)
            if not bank_api_result["valid"]:
                validation_errors.append({
                    "type": "bank_api_error",
                    "code": bank_api_result["code"],
                    "message": bank_api_result["message"]
                })

        return {
            "status": "Invalid" if validation_errors else "Valid",
            "errors": validation_errors,
            "account_number": account,
            "bank_code": bank_code,
            "amount": amount,
            "reference_id": reference_id
        }