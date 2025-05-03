import argparse
import json
import os
import sys
import getpass
from dotenv import load_dotenv
from cryptography.fernet import Fernet

def main():
    # Load .env if present
    load_dotenv()
    parser = argparse.ArgumentParser(description="View decrypted tokens from token_map.json.")
    parser.add_argument("--file", default="output/token_map.json", help="Path to token_map.json")
    parser.add_argument("--key", default=None, help="Fernet key (if not set, will prompt interactively)")
    parser.add_argument("--batch", type=int, default=None, help="Batch index to view (default: all batches)")
    args = parser.parse_args()

    key = args.key
    if not key:
        key = getpass.getpass("Enter Fernet decryption key: ")
    if not key:
        print("ERROR: Fernet key must be supplied via --key or entered interactively.")
        sys.exit(1)

    with open(args.file, "r") as f:
        all_batches = json.load(f)

    fernet = Fernet(key.encode())
    def decrypt_tokens(tokens_blob):
        return json.loads(fernet.decrypt(tokens_blob.encode()).decode())

    if args.batch is not None:
        # Show only one batch
        batch = all_batches[args.batch]
        tokens = decrypt_tokens(batch['tokens'])
        out = {
            'batch_id': batch['batch_id'],
            'timestamp': batch['timestamp'],
            'tokens': tokens
        }
        print(json.dumps(out, indent=2))
    else:
        # Show all batches
        out = []
        for batch in all_batches:
            try:
                tokens = decrypt_tokens(batch['tokens'])
            except Exception as e:
                tokens = f"ERROR decrypting: {e}"
            out.append({
                'batch_id': batch['batch_id'],
                'timestamp': batch['timestamp'],
                'tokens': tokens
            })
        print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
