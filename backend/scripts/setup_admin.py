#!/usr/bin/env python3
"""
Script to run migrations and set up admin users on Railway.

Usage:
    1. Get your Railway DATABASE_URL from the Railway dashboard
    2. Run: DATABASE_URL="postgresql://..." python scripts/setup_admin.py

    Or use Railway CLI:
    railway run python scripts/setup_admin.py
"""

import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command


def main():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set")
        print("\nTo run this script:")
        print("  1. Get your DATABASE_URL from Railway dashboard")
        print("  2. Run: DATABASE_URL='postgresql://...' python scripts/setup_admin.py")
        print("\n  Or use Railway CLI:")
        print("  railway run python scripts/setup_admin.py")
        sys.exit(1)

    print(f"Connecting to database...")
    print(f"URL: {database_url[:50]}...")

    # Run Alembic migrations
    print("\n1. Running Alembic migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(alembic_cfg, "head")
        print("   Migrations completed successfully!")
    except Exception as e:
        print(f"   Migration error: {e}")
        print("   Continuing with admin setup...")

    # Set up admin users
    print("\n2. Setting up admin users...")
    engine = create_engine(database_url)

    admin_emails = [
        "vikram7june@gmail.com",
        "vikram17june@gmail.com",
    ]

    with engine.connect() as conn:
        for email in admin_emails:
            # Check if user exists
            result = conn.execute(
                text("SELECT id, email, is_admin FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()

            if user:
                if user[2]:  # is_admin
                    print(f"   {email} - Already admin")
                else:
                    conn.execute(
                        text("UPDATE users SET is_admin = TRUE WHERE email = :email"),
                        {"email": email}
                    )
                    conn.commit()
                    print(f"   {email} - Set as admin")
            else:
                print(f"   {email} - User not found (they need to login first)")

    print("\n3. Verifying admin users...")
    with engine.connect() as conn:
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

    print("\nDone!")


if __name__ == "__main__":
    main()
