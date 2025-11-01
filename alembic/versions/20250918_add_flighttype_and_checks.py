"""
add flightType and enforce travelType/flightType checks on trips

Revision ID: 20250918_add_flighttype_and_checks
Revises: 20250904_fix_passport_number_column
Create Date: 2025-09-18 00:00:00.000000
"""

from alembic import op  # type: ignore
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250918_add_flighttype_and_checks"
down_revision = "20250904_fix_passport_number_column"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add flightType with server default to allow automatic defaulting
    with op.batch_alter_table("trips") as batch_op:
        try:
            batch_op.add_column(
                sa.Column(
                    "flightType", sa.String(), nullable=True, server_default="class_a"
                )
            )
        except Exception:
            pass

    # Backfill existing rows with a default value
    try:
        op.execute(
            'UPDATE trips SET "flightType" = \'class_a\' WHERE "flightType" IS NULL'
        )
    except Exception:
        # Some engines may not have the column or table; ignore if fails in idempotent runs
        pass

    # Make the column NOT NULL now that a default is in place
    with op.batch_alter_table("trips") as batch_op:
        try:
            batch_op.alter_column(
                "flightType", existing_type=sa.String(), nullable=False
            )
        except Exception:
            pass

    # Add CHECK constraints (engines that support it)
    try:
        op.create_check_constraint(
            "ck_trips_travelType",
            "trips",
            "\"travelType\" IN ('departure', 'arrival')",
        )
    except Exception:
        pass

    try:
        op.create_check_constraint(
            "ck_trips_flightType",
            "trips",
            "\"flightType\" IN ('class_a', 'class_b')",
        )
    except Exception:
        pass


def downgrade() -> None:
    # Drop CHECK constraints if present
    try:
        op.drop_constraint("ck_trips_flightType", "trips", type_="check")
    except Exception:
        pass
    try:
        op.drop_constraint("ck_trips_travelType", "trips", type_="check")
    except Exception:
        pass

    # Drop column
    with op.batch_alter_table("trips") as batch_op:
        try:
            batch_op.drop_column("flightType")
        except Exception:
            pass
