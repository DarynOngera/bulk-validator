from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import pandas as pd
import asyncio
import os
import uuid
import logging
import traceback
from typing import Dict
from concurrent.futures import ThreadPoolExecutor
import concurrent

# === Logging Configuration ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Ensure the output directory exists
os.makedirs('output', exist_ok=True)

# === Security Middleware ===
class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 2_000_000:  # 2MB limit
            return JSONResponse(
                content={"detail": "File too large. Max allowed size is 2MB."},
                status_code=413
            )
        return await call_next(request)

app.add_middleware(LimitUploadSizeMiddleware)

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .validators.account_validator import AccountValidator

# === Helper async validator ===
async def validate_account(account_data: Dict) -> dict:
    validator = AccountValidator()
    return await validator.validate(account_data)

# === Root Endpoint ===
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Bulk Validator API",
        "endpoints": {
            "/upload-csv": "POST endpoint for uploading CSV files",
            "/download/{filename}": "GET endpoint for downloading processed files"
        }
    }

<<<<<<< HEAD
# === Health Check Endpoint ===
@app.get("/health")
async def health():
    return {"status": "ok"}
=======
@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    # Save the uploaded file
    file_path = f"output/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Process the CSV file
    try:
        df = pd.read_csv(file_path)
        # Perform validation or processing here
        total_rows = len(df)
        summary = {
            "total_rows": total_rows,
            "columns": list(df.columns),
        }
        return {
            "message": f"File '{file.filename}' uploaded and processed successfully.",
            "rows": total_rows,
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/download-report")
async def download_report():
    file_path = "output/report.csv"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/csv", filename="report.csv")
    else:
        raise HTTPException(status_code=404, detail="Report not found")
>>>>>>> 712d468fcd2dfc328a93acfc9751f42a6b479770

# === Helper: Common validation and output logic ===
REQUIRED_COLUMNS = ['account_number', 'bank_code', 'amount', 'reference_id']

import hashlib

def tokenize_value(value, prefix):
    # Simple deterministic tokenization using hash (not reversible, but unique per value)
    h = hashlib.sha256(str(value).encode()).hexdigest()[:8]
    return f"{prefix}-{h}"

# In-memory mapping for reference (not exposed)
TOKEN_MAP = {}

from app.reporting import error_breakdown_by_field, per_bank_stats, write_outputs

# === Parallel Validation Logic ===
async def validate_accounts_parallel(df):
    """Process accounts concurrently with 8 workers"""
    validator = AccountValidator()
    
    async def process_row(row):
        try:
            account_data = {
                'account_number': str(row['account_number']),
                'bank_code': str(row['bank_code']),
                'amount': float(row['amount']),
                'reference_id': str(row['reference_id'])
            }
            return await validator.validate(account_data)
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                "status": "Invalid",
                "errors": [{"type": "processing_error", "code": "PE01", "message": str(e)}],
                "account_number": str(row['account_number']),
                "bank_code": str(row['bank_code']),
                "amount": row['amount'],
                "reference_id": str(row['reference_id'])
            }

    # Process in parallel
    loop = asyncio.get_event_loop()
    tasks = [process_row(row) for _, row in df.iterrows()]
    return await asyncio.gather(*tasks)

# === Unified validation and output logic (importable) ===
async def validate_and_output(records, source_type="csv", output_formats=['csv', 'json', 'xlsx']):
    import pandas as pd
    import uuid
    import os
    logger.debug(f"Validating {len(records)} records from {source_type}")
    df = pd.DataFrame(records)
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {', '.join(missing_columns)}")
        return {"detail": f"Input must contain these columns: {', '.join(REQUIRED_COLUMNS)}", "missing_columns": missing_columns}
    # Tokenize sensitive columns
    df['account_token'] = df['account_number'].apply(lambda x: tokenize_value(x, 'ACC'))
    df['reference_token'] = df['reference_id'].apply(lambda x: tokenize_value(x, 'REF'))
    # Store mapping (not exposed)
    for _, row in df.iterrows():
        TOKEN_MAP[row['account_token']] = row['account_number']
        TOKEN_MAP[row['reference_token']] = row['reference_id']
    # Write token map to output/token_map.json (encrypted)
    import json
    import time
    from uuid import uuid4
    from dotenv import load_dotenv
    from cryptography.fernet import Fernet
    import base64
    load_dotenv()
    os.makedirs('output', exist_ok=True)
    token_map_path = 'output/token_map.json'
    batch_id = str(uuid4())
    timestamp = int(time.time())
    # Encrypt only the tokens, not the batch metadata
    key = os.getenv('TOKEN_MAP_KEY')
    if not key:
        raise RuntimeError('TOKEN_MAP_KEY environment variable must be set for encryption.')
    fernet = Fernet(key.encode())
    account_tokens = {k: v for k, v in TOKEN_MAP.items() if k.startswith('ACC-')}
    reference_tokens = {k: v for k, v in TOKEN_MAP.items() if k.startswith('REF-')}
    tokens_dict = {'account_tokens': account_tokens, 'reference_tokens': reference_tokens}
    encrypted_tokens = fernet.encrypt(json.dumps(tokens_dict).encode()).decode()
    batch_entry = {
        'batch_id': batch_id,
        'timestamp': timestamp,
        'tokens': encrypted_tokens
    }
    # Load previous batches (plaintext)
    all_batches = []
    if os.path.exists(token_map_path):
        with open(token_map_path, 'r') as f:
            try:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    all_batches = [loaded]
                elif isinstance(loaded, list):
                    all_batches = loaded
                else:
                    all_batches = []
            except Exception:
                all_batches = []
    all_batches.append(batch_entry)
    with open(token_map_path, 'w') as f:
        json.dump(all_batches, f, indent=2)
    # Validate accounts
    try:
        results = await validate_accounts_parallel(df)
    except Exception as e:
        logger.error(f"Parallel processing error: {str(e)}")
        return JSONResponse(
            {"detail": "Validation system error"},
            status_code=500
        )
    df['status'] = [result['status'] for result in results]
    df['errors'] = [result['errors'] for result in results]
    output_cols = ['account_token', 'bank_code', 'amount', 'reference_token', 'status', 'errors']
    valid_df = df[df['status'] == 'Valid'][output_cols].copy()
    invalid_df = df[df['status'] == 'Invalid'][output_cols].copy()
    total_accounts = len(df)
    valid_accounts = len(valid_df)
    invalid_accounts = len(invalid_df)
    logger.info(f"Validation completed for {total_accounts} accounts")
    logger.info(f"Valid accounts: {valid_accounts}")
    logger.info(f"Invalid accounts: {invalid_accounts}")
    error_breakdown = error_breakdown_by_field(invalid_df)
    per_bank = per_bank_stats(df)
    summary = {
        "total_accounts": total_accounts,
        "valid_accounts": valid_accounts,
        "invalid_accounts": invalid_accounts,
        "invalid_error_types": error_breakdown,
        "per_bank_stats": per_bank
    }
    base_filename = f"accounts_{uuid.uuid4().hex}"
    output_paths = write_outputs(valid_df, invalid_df, summary, base_filename, formats=output_formats)
    return {
        "validation_summary": summary,
        "files": output_paths,
        "tokenization_notice": "Sensitive fields (account_number, reference_id) have been tokenized in all outputs. Real values are never logged or exposed via API."
    }

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

<<<<<<< HEAD
# === Route: Upload XML ===
import xml.etree.ElementTree as ET
@app.post("/upload-xml")
async def upload_xml(file: UploadFile = File(...)):
    try:
        xml_content = await file.read()
        root = ET.fromstring(xml_content)
        records = []
        for elem in root.findall('.//record'):
            record = {col: elem.findtext(col, default='') for col in REQUIRED_COLUMNS}
            # Convert amount to float if possible
            try:
                record['amount'] = float(record['amount'])
            except Exception:
                record['amount'] = 0.0
            records.append(record)
        return await validate_and_output(records, source_type="xml")
    except Exception as e:
        logger.error(f"Error processing XML: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return JSONResponse({
            "detail": "Error processing XML",
            "error": str(e)
        }, status_code=500)

# === Route: Download CSV ===
@app.get("/download/{filename}")
async def download_file(filename: str):
    path = f"./{filename}"
    if os.path.exists(path):
        return FileResponse(path, filename=filename)
    return JSONResponse({"detail": "File not found."}, status_code=404)

# === Secure Admin Token Lookup Endpoint ===
from fastapi import Query, Header, Depends
from fastapi.responses import JSONResponse
from app.security import require_role

@app.post("/lookup-token")
async def lookup_token(token: str = Query(...), role: str = Depends(require_role("admin", "auditor"))):
    import os
    import json
    from dotenv import load_dotenv
    load_dotenv()
    # Load token map (only 'tokens' field is encrypted)
    token_map_path = 'output/token_map.json'
    if not os.path.exists(token_map_path):
        return JSONResponse({"detail": "Token map not found."}, status_code=404)
    with open(token_map_path, 'r') as f:
        token_map = json.load(f)
    from cryptography.fernet import Fernet
    key = os.getenv('TOKEN_MAP_KEY')
    if not key:
        return JSONResponse({"detail": "TOKEN_MAP_KEY environment variable must be set for encryption/decryption."}, status_code=500)
    fernet = Fernet(key)
    for batch in token_map.get('batches', []):
        encrypted_tokens = batch.get('tokens')
        if not encrypted_tokens:
            continue
        try:
            tokens_dict = json.loads(fernet.decrypt(encrypted_tokens.encode()).decode())
        except Exception:
            continue
        if token.startswith('ACC-') and token in tokens_dict.get('account_tokens', {}):
            return {"token": token, "real_value": tokens_dict['account_tokens'][token], "batch_id": batch['batch_id'], "timestamp": batch['timestamp']}
        if token.startswith('REF-') and token in tokens_dict.get('reference_tokens', {}):
            return {"token": token, "real_value": tokens_dict['reference_tokens'][token], "batch_id": batch['batch_id'], "timestamp": batch['timestamp']}
    return JSONResponse({"detail": "Token not found."}, status_code=404)
=======
def test_upload_csv():
    with open("seed_accounts.csv", "rb") as file:
        response = client.post("/upload-csv", files={"file": ("seed_accounts.csv", file, "text/csv")})
    assert response.status_code == 200
    assert response.json()["message"] == "File 'seed_accounts.csv' uploaded and processed successfully."
    assert response.json()["rows"] == 10000
>>>>>>> 712d468fcd2dfc328a93acfc9751f42a6b479770
