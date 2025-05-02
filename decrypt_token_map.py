import os
import json
from cryptography.fernet import Fernet
import argparse

def main():
    parser = argparse.ArgumentParser(description="Decrypt an encrypted token_map.json file.")
    parser.add_argument("--file", default="output/token_map.json", help="Path to encrypted token_map.json")
    parser.add_argument("--key", default=None, help="Fernet key (if not set, will read TOKEN_MAP_KEY from env)")
    parser.add_argument("--out", default=None, help="Output file for decrypted JSON (prints to stdout if not set)")
    args = parser.parse_args()

    key = args.key or os.getenv("TOKEN_MAP_KEY")
    if not key:
        print("ERROR: Fernet key must be supplied via --key or TOKEN_MAP_KEY env var.")
        exit(1)

    with open(args.file, "rb") as f:
        data = f.read()
        try:
            fernet = Fernet(key.encode())
            decrypted = fernet.decrypt(data)
            token_map = json.loads(decrypted.decode())
        except Exception as e:
            print(f"ERROR: Failed to decrypt. {e}")
            exit(2)

    if args.out:
        with open(args.out, "w") as out_f:
            json.dump(token_map, out_f, indent=2)
        print(f"Decrypted token map written to {args.out}")
    else:
        print(json.dumps(token_map, indent=2))

if __name__ == "__main__":
    main()
