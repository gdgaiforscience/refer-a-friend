import sqlite3
import os
import argparse
import csv
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load your local .env file containing the ENCRYPTION_KEY
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is missing.")

cipher_suite = Fernet(SECRET_KEY.encode())

def export_decrypted_csv(db_path: str, out_path: str):
    """Fetches all referrals, decrypts emails, and writes to a CSV."""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at '{db_path}'")
        return

    # Connect directly via sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query the encrypted schema
    try:
        cursor.execute("SELECT id, encrypted_email, event_path, referral_code, created_at FROM referrals")
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        print("Ensure you are targeting the updated database containing the 'encrypted_email' column.")
        conn.close()
        return

    conn.close()

    print(f"Found {len(rows)} referrals. Decrypting and exporting to {out_path}...")

    success_count = 0
    error_count = 0

    # Write to CSV
    with open(out_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        
        # Write headers matching your original schema
        writer.writerow(['id', 'member_email', 'event_path', 'referral_code', 'created_at'])

        for row in rows:
            row_id, encrypted_email, event_path, referral_code, created_at = row
            
            try:
                # Decrypt the email payload
                real_email = cipher_suite.decrypt(encrypted_email.encode('utf-8')).decode('utf-8')
                writer.writerow([row_id, real_email, event_path, referral_code, created_at])
                success_count += 1
            except Exception as e:
                print(f"Error decrypting row ID {row_id}: {e}")
                # Write the row anyway, but insert a failure notice to prevent data loss of other columns
                writer.writerow([row_id, "DECRYPTION_FAILED", event_path, referral_code, created_at])
                error_count += 1

    print("-" * 40)
    print("Export Complete!")
    print(f"Output File:          {out_path}")
    print(f"Successfully Decrypted: {success_count}")
    if error_count > 0:
        print(f"Failed to Decrypt:      {error_count}")
    print("-" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk Offline PII Decryption to CSV")
    
    parser.add_argument(
        "--db", 
        dest="db_path", 
        required=True, 
        help="Path to the local SQLite database file (e.g., ./data/gdg_referrals.db)"
    )
    
    parser.add_argument(
        "--out", 
        dest="out_path", 
        default="decrypted_referrals.csv", 
        help="Path to the output CSV file (default: decrypted_referrals.csv)"
    )
    
    args = parser.parse_args()
    
    export_decrypted_csv(args.db_path, args.out_path)