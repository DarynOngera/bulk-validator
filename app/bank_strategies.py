import random
import string

# --- Example Account Generation Algorithms ---
def gen_account_001():
    # Simple 10-digit numeric, Luhn checksum
    base = ''.join(random.choices(string.digits, k=9))
    checksum = luhn_checksum(base)
    return base + checksum

def gen_account_002():
    # 8 chars: 2 uppercase letters + 6 digits
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    digits = ''.join(random.choices(string.digits, k=6))
    return letters + digits

def gen_account_003():
    # 12 digits, starts with '77', ends with random 2
    middle = ''.join(random.choices(string.digits, k=8))
    end = ''.join(random.choices(string.digits, k=2))
    return '77' + middle + end

# --- Example Validation Algorithms ---
def validate_account_001(acct: str) -> bool:
    # Must be 10 digits, valid Luhn
    return len(acct) == 10 and acct.isdigit() and luhn_check(acct)

def validate_account_002(acct: str) -> bool:
    # 2 letters + 6 digits
    return (
        len(acct) == 8 and
        acct[:2].isalpha() and acct[:2].isupper() and
        acct[2:].isdigit()
    )

def validate_account_003(acct: str) -> bool:
    # 12 digits, starts with '77'
    return (
        len(acct) == 12 and
        acct.startswith('77') and
        acct.isdigit()
    )

# --- Utility: Luhn checksum ---
def luhn_checksum(base: str) -> str:
    digits = [int(d) for d in base]
    s = sum(digits[-1::-2]) + sum(sum(divmod(d*2,10)) for d in digits[-2::-2])
    return str((10 - (s % 10)) % 10)

def luhn_check(acct: str) -> bool:
    digits = [int(d) for d in acct]
    s = sum(digits[-1::-2]) + sum(sum(divmod(d*2,10)) for d in digits[-2::-2])
    return s % 10 == 0

# --- Registry ---
BANK_GENERATORS = {
    '001': gen_account_001,
    '002': gen_account_002,
    '003': gen_account_003,
}

BANK_VALIDATORS = {
    '001': validate_account_001,
    '002': validate_account_002,
    '003': validate_account_003,
}
