import sqlite3

def migrate():
    db = sqlite3.connect('gdg_referrals.db')
    
    # Create the new table with the UNIQUE constraint
    db.execute("""
    CREATE TABLE IF NOT EXISTS referrals_new (
        id INTEGER PRIMARY KEY,
        member_email VARCHAR NOT NULL,
        event_path VARCHAR NOT NULL,
        referral_code VARCHAR NOT NULL,
        created_at DATETIME,
        UNIQUE(member_email, event_path),
        UNIQUE(referral_code)
    )
    """)
    
    # Insert existing data, ignoring duplicates to enforce the new constraint cleanly
    # Keeping the earliest ID for duplicates.
    db.execute("""
    INSERT OR IGNORE INTO referrals_new (id, member_email, event_path, referral_code, created_at)
    SELECT id, member_email, event_path, referral_code, created_at FROM referrals ORDER BY id ASC
    """)
    
    # Drop the old table and rename the new one
    db.execute("DROP TABLE referrals")
    db.execute("ALTER TABLE referrals_new RENAME TO referrals")
    
    # Recreate the indices
    db.execute("CREATE INDEX IF NOT EXISTS ix_referrals_member_email ON referrals (member_email)")
    db.execute("CREATE INDEX IF NOT EXISTS ix_referrals_referral_code ON referrals (referral_code)")
    db.execute("CREATE INDEX IF NOT EXISTS ix_referrals_id ON referrals (id)")
    
    db.commit()
    db.close()
    
    print("Database migration completed successfully.")

if __name__ == "__main__":
    migrate()
