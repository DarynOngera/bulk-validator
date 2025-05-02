import os
import subprocess
import time

# Configuration
large_file = "large_file.csv"
num_records = 20000  # Number of records for the large file
workers = 8  # Number of parallel workers

# Step 1: Generate a large CSV file
def generate_large_file():
    print(f"Generating a large CSV file with {num_records} records...")
    with open(large_file, "w") as f:
        # Write header
        f.write("account_number,bank_code,amount,reference_id\n")
        # Write dummy data
        for i in range(num_records):
            f.write(f"ACC{i:08d},001,{i * 10.5:.2f},REF{i:08d}\n")
    print(f"Large CSV file '{large_file}' generated successfully.")

# Step 2: Process the file in parallel
def process_file_in_parallel():
    print(f"Processing '{large_file}' with {workers} workers...")
    start_time = time.time()
    command = [
        "python", "batch_ingest.py", large_file, "--type", "csv"
    ]
    subprocess.run(command, check=True)
    end_time = time.time()
    print(f"Processing completed in {end_time - start_time:.2f} seconds.")

# Step 3: Verify output
def verify_output():
    output_dir = "output"
    if not os.path.exists(output_dir):
        print(f"Output directory '{output_dir}' not found!")
        return
    print(f"Checking output files in '{output_dir}'...")
    for file in os.listdir(output_dir):
        print(f" - {file}")

# Main function
if __name__ == "__main__":
    generate_large_file()
    process_file_in_parallel()
    verify_output()