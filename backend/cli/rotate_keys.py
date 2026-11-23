"""
Encryption key rotation tool.

Re-encrypts all sensitive database fields under the current ENCRYPTION_KEY.
Set ENCRYPTION_KEY to the new key and ENCRYPTION_KEY_PREVIOUS to the old key
in your .env file before running.

Usage:
    python -m backend.cli.rotate_keys
    python -m backend.cli.rotate_keys --dry-run
"""

import argparse
import sys

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.encryption import rotate_value


def _sync_database_url() -> str:
    return settings.DATABASE_URL.replace("+aiosqlite", "")


def run(dry_run: bool = False) -> None:
    if not settings.ENCRYPTION_KEY_PREVIOUS:
        print("ERROR: ENCRYPTION_KEY_PREVIOUS is not set.")
        print("Set it to the old key in .env before running rotation.")
        sys.exit(1)

    engine = create_engine(_sync_database_url())

    with Session(engine) as session:
        session.execute(text("PRAGMA foreign_keys=ON"))

        rotated = 0
        errors = 0

        rows = session.execute(
            text("SELECT id, username, totp_secret_encrypted FROM users")
        ).fetchall()

        for row in rows:
            user_id, username, encrypted_val = row

            if not encrypted_val:
                continue

            try:
                new_val, changed = rotate_value(
                    encrypted_val,
                    settings.ENCRYPTION_KEY,
                    settings.ENCRYPTION_KEY_PREVIOUS,
                )

                if changed:
                    if not dry_run:
                        session.execute(
                            text(
                                "UPDATE users SET totp_secret_encrypted = :val WHERE id = :id"
                            ),
                            {"val": new_val, "id": user_id},
                        )

                    rotated += 1
                    print(f"  Rotated: users.totp_secret_encrypted for {username}")

                else:
                    print(f"  Skipped: users.totp_secret_encrypted for {username} (already current)")

            except Exception as e:
                errors += 1
                print(f"  FAILED: users.totp_secret_encrypted for {username}: {e}")

        rows = session.execute(
            text("SELECT id, smtp_password_encrypted FROM settings")
        ).fetchall()

        for row in rows:
            settings_id, encrypted_val = row

            if not encrypted_val:
                continue

            try:
                new_val, changed = rotate_value(
                    encrypted_val,
                    settings.ENCRYPTION_KEY,
                    settings.ENCRYPTION_KEY_PREVIOUS,
                )

                if changed:
                    if not dry_run:
                        session.execute(
                            text(
                                "UPDATE settings SET smtp_password_encrypted = :val WHERE id = :id"
                            ),
                            {"val": new_val, "id": settings_id},
                        )

                    rotated += 1
                    print(f"  Rotated: settings.smtp_password_encrypted (id={settings_id})")

                else:
                    print(f"  Skipped: settings.smtp_password_encrypted (id={settings_id}, already current)")

            except Exception as e:
                errors += 1
                print(f"  FAILED: settings.smtp_password_encrypted (id={settings_id}): {e}")

        if not dry_run:
            session.commit()

    print()
    print(f"{'[DRY RUN] ' if dry_run else ''}Rotation complete: {rotated} rotated, {errors} errors")

    if errors:
        print("WARNING: Some values could not be decrypted with either key.")
        sys.exit(1)

    if not dry_run and rotated > 0:
        print("You can now remove ENCRYPTION_KEY_PREVIOUS from your .env file.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rotate encryption keys")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be rotated without making changes",
    )
    args = parser.parse_args()

    run(dry_run=args.dry_run)
