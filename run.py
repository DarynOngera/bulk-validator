import typer
import subprocess
import sys

app = typer.Typer(help="Unified CLI for Bulk Validator")

@app.command()
def api():
    """Start the API server (dev mode)"""
    subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload"])

@app.command()
def seed():
    """Seed demo account data"""
    subprocess.run([sys.executable, "seed_accounts.py"])

@app.command()
def batch(file: str = "seed_accounts.json", type: str = "json"):
    """Run batch ingest on a file"""
    subprocess.run([sys.executable, "batch_ingest.py", file, "--type", type])

@app.command()
def view_tokens(file: str = "output/token_map.json"):
    """View decrypted tokens from the token map"""
    subprocess.run([sys.executable, "view_decrypted_token_map.py", "--file", file])

@app.command()
def docker():
    """Run using Docker Compose (API + Mailhog)"""
    subprocess.run(["docker-compose", "up", "--build"])

if __name__ == "__main__":
    app()
