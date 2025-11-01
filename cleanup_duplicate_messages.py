#!/usr/bin/env python3
"""
Script to clean up duplicate messages in the database.
This script will remove duplicate messages, keeping only the latest one.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from api.database.database import SessionLocal, engine
from api.models.message_model import Message
from sqlalchemy import func


def cleanup_duplicate_messages():
    """Remove duplicate messages, keeping the latest one based on created_at."""
    db = SessionLocal()
    try:
        # Find duplicate message IDs
        duplicate_ids = (
            db.query(Message.id)
            .group_by(Message.id)
            .having(func.count(Message.id) > 1)
            .all()
        )

        if not duplicate_ids:
            print("No duplicate messages found.")
            return

        print(f"Found {len(duplicate_ids)} duplicate message IDs.")

        for (message_id,) in duplicate_ids:
            # Get all messages with this ID, ordered by created_at (newest first)
            messages = (
                db.query(Message)
                .filter(Message.id == message_id)
                .order_by(Message.created_at.desc())
                .all()
            )

            if len(messages) > 1:
                # Keep the first (newest) message, delete the rest
                messages_to_delete = messages[1:]
                for msg in messages_to_delete:
                    print(
                        f"Deleting duplicate message: {msg.id} (created: {msg.created_at})"
                    )
                    db.delete(msg)

        db.commit()
        print("Duplicate messages cleaned up successfully.")

    except Exception as e:
        print(f"Error cleaning up duplicate messages: {e}")
        db.rollback()
    finally:
        db.close()


def show_message_stats():
    """Show statistics about messages in the database."""
    db = SessionLocal()
    try:
        total_messages = db.query(Message).count()
        unique_ids = db.query(Message.id).distinct().count()
        duplicates = total_messages - unique_ids

        print(f"Total messages: {total_messages}")
        print(f"Unique message IDs: {unique_ids}")
        print(f"Duplicate messages: {duplicates}")

    except Exception as e:
        print(f"Error getting message stats: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Message Database Cleanup Tool")
    print("=" * 40)

    # Show current stats
    print("\nCurrent message statistics:")
    show_message_stats()

    # Ask for confirmation
    response = input("\nDo you want to clean up duplicate messages? (y/N): ")
    if response.lower() in ["y", "yes"]:
        print("\nCleaning up duplicate messages...")
        cleanup_duplicate_messages()

        print("\nUpdated message statistics:")
        show_message_stats()
    else:
        print("Cleanup cancelled.")
