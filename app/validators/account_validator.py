# app/validators/account_validator.py

import re
from typing import Dict
from app.bank_strategies import BANK_VALIDATORS

class AccountValidator:
    def __init__(self):
        # Realistic bank codes
        self.valid_bank_codes = ["001", "002", "003", "044", "058", "070", "232", "082", "214", "215"]
        self.validation_rules = [
            {
                "name": "iban_format_or_checksum",
                "rule": lambda x: self._looks_like_iban(x) and not self._validate_iban(x),
                "message": "Invalid IBAN format or checksum"
            },
            {
                "name": "length_error",
                "rule": lambda x: not self._looks_like_iban(x) and not (8 <= len(x) <= 12),
                "message": "Account number must be 8-12 characters (unless IBAN)"
            },
            {
                "name": "alphanumeric_format",
                "rule": lambda x: not self._looks_like_iban(x) and not x.isalnum(),
                "message": "Account number must be alphanumeric (unless IBAN)"
            },
            {
                "name": "bank_code_validation",
                "rule": lambda x, bank_code: not self._looks_like_iban(x) and bank_code not in self.valid_bank_codes,
                "message": "Invalid bank code"
            },
            {
                "name": "luhn_checksum",
                "rule": lambda x: not self._looks_like_iban(x) and (x.isdigit() and len(x) == 10 and not self._validate_checksum(x)),
                "message": "Invalid account number checksum (for 10-digit numeric only)"
            },
            {
                "name": "amount_validation",
                "rule": lambda x, amount: not self._validate_amount(amount),
                "message": "Invalid amount"
            },
            {
                "name": "reference_id_validation",
                "rule": lambda x, amount, reference_id: not reference_id,
                "message": "Reference ID must be non-empty"
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
                        "message": rule["message"]
                    })
            elif rule["name"] == "amount_validation":
                if rule["rule"](account, amount):
                    validation_errors.append({
                        "type": rule["name"],
                        "message": rule["message"]
                    })
            elif rule["name"] == "reference_id_validation":
                if rule["rule"](account, amount, reference_id):
                    validation_errors.append({
                        "type": rule["name"],
                        "message": rule["message"]
                    })
            else:
                if rule["rule"](account):
                    validation_errors.append({
                        "type": rule["name"],
                        "message": rule["message"]
                    })

        return {
            "status": "Invalid" if validation_errors else "Valid",
            "errors": validation_errors,
            "account_number": account,
            "bank_code": bank_code,
            "amount": amount,
            "reference_id": reference_id
        }
