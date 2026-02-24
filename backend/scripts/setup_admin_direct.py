#!/usr/bin/env python3
"""
Direct SQL script to set up admin users on Railway.
Bypasses Alembic and runs raw SQL.
"""

import os
import sys
from sqlalchemy import create_engine, text


def main():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)

    print(f"Connecting to database...")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Step 1: Add is_admin column if it doesn't exist
        print("\n1. Adding is_admin column to users table...")
        try:
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE
            """))
            conn.commit()
            print("   Column added successfully!")
        except Exception as e:
            print(f"   Note: {e}")
            conn.rollback()

        # Step 2: Create pending_ecosystem_changes table if it doesn't exist
        print("\n2. Creating pending_ecosystem_changes table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pending_ecosystem_changes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    card_id UUID REFERENCES cards(id) ON DELETE CASCADE NOT NULL,
                    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE NOT NULL,
                    benefit_rate NUMERIC(5, 2) NOT NULL,
                    benefit_type VARCHAR(50) NOT NULL,
                    description TEXT,
                    source_url VARCHAR(500),
                    change_type VARCHAR(20) NOT NULL,
                    old_values JSONB,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    scraped_at TIMESTAMP DEFAULT NOW(),
                    reviewed_at TIMESTAMP,
                    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()
            print("   Table created successfully!")
        except Exception as e:
            print(f"   Note: {e}")
            conn.rollback()

        # Step 3: Create indexes
        print("\n3. Creating indexes...")
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_pending_ecosystem_changes_status
                ON pending_ecosystem_changes(status)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_pending_ecosystem_changes_card_id
                ON pending_ecosystem_changes(card_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_pending_ecosystem_changes_brand_id
                ON pending_ecosystem_changes(brand_id)
            """))
            conn.commit()
            print("   Indexes created successfully!")
        except Exception as e:
            print(f"   Note: {e}")
            conn.rollback()

        # Step 4: Set up admin users
        print("\n4. Setting up admin users...")
        admin_emails = [
            "vikram7june@gmail.com",
            "vikram17june@gmail.com",
        ]

        for email in admin_emails:
            result = conn.execute(
                text("SELECT id, email FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()

            if user:
                conn.execute(
                    text("UPDATE users SET is_admin = TRUE WHERE email = :email"),
                    {"email": email}
                )
                conn.commit()
                print(f"   {email} - Set as admin")
            else:
                print(f"   {email} - User not found (they need to login first)")

        # Step 5: Verify admin users
        print("\n5. Verifying admin users...")
        result = conn.execute(
            text("SELECT email, is_admin FROM users WHERE is_admin = TRUE")
        )
        admins = result.fetchall()

        if admins:
            print("   Current admins:")
            for admin in admins:
                print(f"   - {admin[0]}")
        else:
            print("   No admin users found")

        # Step 6: Update alembic_version to mark migrations as complete
        print("\n6. Updating alembic version...")
        try:
            # Check current version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.fetchone()
            print(f"   Current version: {current[0] if current else 'None'}")

            # Update to latest
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('20260224140000')"))
            conn.commit()
            print("   Updated to version: 20260224140000")
        except Exception as e:
            print(f"   Note: {e}")
            conn.rollback()

    print("\nDone!")


if __name__ == "__main__":
    main()
