import os
import argparse
import pandas as pd
import ijson
import xml.etree.ElementTree as ET
from app.main import validate_and_output, REQUIRED_COLUMNS
import asyncio
import json

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
    import os
    from app.email_notify import send_validation_report_email
    parser = argparse.ArgumentParser(description='Bulk Validator Batch Ingest')
    parser.add_argument('file', help='Input file path (CSV, JSON, XML)')
    parser.add_argument('--type', choices=['csv', 'json', 'xml'], required=True)
    parser.add_argument('--notify', help='Notification email address (overrides EMAIL_NOTIFY_TO env var)', default=None)
    args = parser.parse_args()
    ext = args.type
    path = args.file
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
    all_results = []
    for records in batcher:
        print(f"Processing chunk {chunk_num+1} ({len(records)} records)...")
        result = loop.run_until_complete(validate_and_output(records, source_type=ext))
        all_results.append(result)
        chunk_num += 1
    print("Batch processing complete.")
    # Email notification
    notify_to = args.notify or os.getenv('EMAIL_NOTIFY_TO')
    if notify_to:
        # Use last result for summary and files
        summary = all_results[-1]['validation_summary']
        files = all_results[-1]['files']
        summary_txt = json.dumps(summary, indent=2)
        attachments = list(files.values())
        print(f"Sending notification to {notify_to} ...")
        send_validation_report_email(
            recipient=notify_to,
            subject="Bulk Validation Complete",
            body=f"Bulk validation has completed.\n\nSummary:\n{summary_txt}",
            attachments=attachments
        )
        print("Notification sent.")

if __name__ == '__main__':
    main()
