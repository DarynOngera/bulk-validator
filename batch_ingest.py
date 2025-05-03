import os
from dotenv import load_dotenv
load_dotenv()
import argparse
import pandas as pd
import ijson
import xml.etree.ElementTree as ET
from app.main import validate_and_output, REQUIRED_COLUMNS
import asyncio
import json
import logging
import time

# Ensure the output directory exists
os.makedirs('output', exist_ok=True)

# Configure logging
log_file_path = os.path.abspath('output/batch_processing.log')
logger = logging.getLogger()  # Get the root logger
logger.setLevel(logging.INFO)

# Create a file handler
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)

# Create a console handler (optional, for debugging)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Define a log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Test logging
logger.info("Logging initialized successfully.")

CHUNK_SIZE = 1000

def process_csv(path):
    for chunk in pd.read_csv(path, dtype=str, chunksize=CHUNK_SIZE):
        records = chunk.to_dict(orient='records')
        yield records

def process_json(path):
    with open(path, 'r') as f:
        parser = ijson.items(f, 'item')
        batch = []
        for rec in parser:
            batch.append(rec)
            if len(batch) >= CHUNK_SIZE:
                yield batch
                batch = []
        if batch:
            yield batch

def process_xml(path):
    context = ET.iterparse(path, events=("end",))
    batch = []
    for event, elem in context:
        if elem.tag == 'record':
            record = {col: elem.findtext(col, default='') for col in REQUIRED_COLUMNS}
            batch.append(record)
            if len(batch) >= CHUNK_SIZE:
                yield batch
                batch = []
            elem.clear()
    if batch:
        yield batch

def main():
    parser = argparse.ArgumentParser(description='Bulk Validator Batch Ingest')
    parser.add_argument('file', help='Input file path (CSV, JSON, XML)')
    parser.add_argument('--type', choices=['csv', 'json', 'xml'], required=True)
    parser.add_argument('--notify', help='Notification email address (overrides EMAIL_NOTIFY_TO env var)', default=None)
    args = parser.parse_args()
    ext = args.type
    path = args.file

    # Start timer
    start_time = time.time()

    if ext == 'csv':
        batcher = process_csv(path)
    elif ext == 'json':
        batcher = process_json(path)
    elif ext == 'xml':
        batcher = process_xml(path)
    else:
        raise ValueError('Unsupported file type')

    loop = asyncio.get_event_loop()
    chunk_num = 0
    total_records = 0
    total_valid = 0
    total_invalid = 0
    all_results = []

    for records in batcher:
        chunk_num += 1
        total_records += len(records)
        print(f"Processing chunk {chunk_num} ({len(records)} records)...")
        logger.info(f"Processing chunk {chunk_num} ({len(records)} records)...")
        result = loop.run_until_complete(validate_and_output(records, source_type=ext))
        all_results.append(result)

        # Debug: Log the result structure
        logger.info(f"Result structure: {result}")

        # Update valid and invalid counts
        validation_summary = result.get("validation_summary", {})
        total_valid += validation_summary.get("valid_accounts", 0)
        total_invalid += validation_summary.get("invalid_accounts", 0)

    # Example: Writing a report to output/report.csv
    report_path = "output/report.csv"
    df = pd.DataFrame(all_results)
    df.to_csv(report_path, index=False)

    print("Batch processing complete.")
<<<<<<< HEAD
    # Email notification
    notify_to = args.notify or os.getenv('EMAIL_NOTIFY_TO')
    if notify_to:
        # Use last result for summary and files
        summary = all_results[-1]['validation_summary']
        files = all_results[-1]['files']
        attachments = list(files.values())
        print(f"Sending notification to {notify_to} ...")
        send_validation_report_email(
            recipient=notify_to,
            subject="Bulk Validation Complete",
            body=(
                "Dear User,\n\n"
                "Your batch validation request has been completed successfully. "
                "Please find the results attached to this email.\n\n"
                "Best regards,\nBulk Validator System"
            ),
            attachments=attachments
        )
        print("Notification sent.")
=======
    logger.info("Batch processing complete.")

    # End timer and log total time
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"Total chunks processed: {chunk_num}")
    logger.info(f"Total records processed: {total_records}")
    logger.info(f"Total valid records: {total_valid}")
    logger.info(f"Total invalid records: {total_invalid}")
    logger.info(f"Total processing time: {total_time:.2f} seconds")
    print(f"Total chunks processed: {chunk_num}")
    print(f"Total records processed: {total_records}")
    print(f"Total valid records: {total_valid}")
    print(f"Total invalid records: {total_invalid}")
    print(f"Total processing time: {total_time:.2f} seconds")
>>>>>>> 712d468fcd2dfc328a93acfc9751f42a6b479770

if __name__ == '__main__':
    main()
