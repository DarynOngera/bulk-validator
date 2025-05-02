import csv
import random
import string

# Configuration
total_records = 500
valid_ratio = 0.6  # 60% valid, 40% invalid
output_csv = "seed_accounts.csv"

# IBAN country codes and lengths (subset for demo)
IBAN_COUNTRIES = {
    'GB': 22, 'DE': 22, 'FR': 27, 'ES': 24, 'IT': 27,
    'NL': 18, 'BE': 16, 'CH': 21, 'PL': 28, 'SE': 24
}

# Helper functions
def random_digits(n):
    return ''.join(random.choices(string.digits, k=n))

def luhn_checksum(num_str):
    digits = [int(d) for d in num_str]
    sum_ = sum(digits[-1::-2]) + sum(sum(divmod(d*2,10)) for d in digits[-2::-2])
    return sum_ % 10

def random_alphanum_strict(n):
    # Alphanumeric, no symbols
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def generate_luhn_account():
    # Generate a 9-digit base, compute the 10th digit
    base = random_digits(9)
    for last in range(10):
        candidate = base + str(last)
        if luhn_checksum(candidate) == 0:
            return candidate
    # fallback (shouldn't happen)
    return base + '0'

def generate_account_number():
    # 50% numeric, 50% alphanumeric, length 8-12
    length = random.choice([8, 9, 10, 11, 12])
    if random.random() < 0.5:
        # Numeric, for 10-digit use valid Luhn
        if length == 10:
            return generate_luhn_account()
        return random_digits(length)
    else:
        return random_alphanum_strict(length)

def random_letters(n):
    return ''.join(random.choices(string.ascii_uppercase, k=n))

def random_alphanum(n):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def iban_checksum(iban_body):
    # Move first 4 chars to end, convert letters to numbers, compute MOD-97
    rearranged = iban_body[4:] + iban_body[:4]
    numerized = ''
    for c in rearranged:
        if c.isdigit():
            numerized += c
        else:
            numerized += str(ord(c.upper()) - 55)
    checksum = 98 - (int(numerized) % 97)
    return f"{checksum:02d}"

def generate_valid_iban():
    country = random.choice(list(IBAN_COUNTRIES.keys()))
    length = IBAN_COUNTRIES[country]
    # 2-letter country, 2 check, rest alphanum
    bban_length = length - 4
    bban = random_alphanum(bban_length)
    temp_iban = country + "00" + bban
    check = iban_checksum(temp_iban)
    return country + check + bban

def generate_invalid_iban():
    country = random.choice(list(IBAN_COUNTRIES.keys()))
    length = IBAN_COUNTRIES[country]
    bban_length = length - 4
    bban = random_alphanum(bban_length)
    # Purposely wrong checksum or length
    if random.random() < 0.5:
        # Wrong checksum
        check = f"{random.randint(0, 97):02d}"
        while check == iban_checksum(country + "00" + bban):
            check = f"{random.randint(0, 97):02d}"
        return country + check + bban
    else:
        # Wrong length
        wrong_length = length + random.choice([-3, -2, -1, 1, 2, 3])
        bban = random_alphanum(max(1, wrong_length - 4))
        check = iban_checksum(country + "00" + bban)
        return country + check + bban

def make_valid_account(idx, used_refs):
    # 20% chance to generate valid IBAN
    if random.random() < 0.2:
        acct = generate_valid_iban()
        bank = ""  # IBANs may not use local bank_code
    else:
        acct = generate_account_number()
        bank = random.choice(["001", "002", "003", "044", "058", "070", "232"])
    amt = round(random.uniform(50, 500000), 2)
    ref = f"TX{random.randint(100000,999999)}"
    # Ensure unique reference_id
    while ref in used_refs:
        ref = f"TX{random.randint(100000,999999)}"
    used_refs.add(ref)
    return {
        "account_number": acct,
        "bank_code": bank,
        "amount": amt,
        "reference_id": ref
    }

def make_invalid_account(idx, used_refs):
    error_type = random.choice([
        "short_account", "long_account", "symbols", "bad_bank", "bad_amount", "empty_ref", "dup_ref", "invalid_iban"])
    # Account number
    if error_type == "invalid_iban":
        acct = generate_invalid_iban()
        bank = ""
    elif error_type == "short_account":
        acct = random_alphanum_strict(random.randint(5, 7))
        bank = random.choice(["001", "002", "003", "044", "058", "070", "232"])
    elif error_type == "long_account":
        acct = random_alphanum_strict(random.randint(13, 16))
        bank = random.choice(["001", "002", "003", "044", "058", "070", "232"])
    elif error_type == "symbols":
        acct = ''.join(random.choices(string.ascii_uppercase + string.digits + "@#$", k=random.randint(8, 12)))
        bank = random.choice(["001", "002", "003", "044", "058", "070", "232"])
    else:
        acct = generate_account_number()
        bank = random.choice(["999", "ABC", "00", "004"]) if error_type == "bad_bank" else random.choice(["001", "002", "003", "044", "058", "070", "232"])
    # Amount
    if error_type == "bad_amount":
        amt = random.choice([-100, 0, 1e8])
    else:
        amt = round(random.uniform(50, 500000), 2)
    # Reference ID
    if error_type == "empty_ref":
        ref = ""
    elif error_type == "dup_ref" and used_refs:
        ref = random.choice(list(used_refs))
    else:
        ref = f"BAD{random.randint(100000,999999)}"
        used_refs.add(ref)
    return {
        "account_number": acct,
        "bank_code": bank,
        "amount": amt,
        "reference_id": ref
    }

def main():
    records = []
    num_valid = int(total_records * valid_ratio)
    num_invalid = total_records - num_valid
    used_refs = set()
    for i in range(num_valid):
        records.append(make_valid_account(i, used_refs))
    for i in range(num_invalid):
        records.append(make_invalid_account(i, used_refs))
    random.shuffle(records)
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["account_number", "bank_code", "amount", "reference_id"])
        writer.writeheader()
        writer.writerows(records)
    print(f"Seed file generated: {output_csv} ({len(records)} records)")

if __name__ == "__main__":
    main()
