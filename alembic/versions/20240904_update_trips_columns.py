"""
add travelType, passengerCount, additionalInfo to trips

Revision ID: 20240904_update_trips_columns
Revises: 20240904_drop_flightnumber
Create Date: 2025-09-04 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240904_update_trips_columns"
down_revision = "20240904_drop_flightnumber"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("trips") as batch_op:
        try:
            batch_op.add_column(
                sa.Column(
                    "travelType",
                    sa.String(),
                    nullable=False,
                    server_default="departure",
                )
            )
            batch_op.add_column(
                sa.Column(
                    "passengerCount", sa.Integer(), nullable=False, server_default="0"
                )
            )
            batch_op.add_column(
                sa.Column(
                    "additionalInfo", sa.String(), nullable=True, server_default=""
                )
            )
        finally:
            # Remove server defaults after data migration
            op.execute("ALTER TABLE trips ALTER COLUMN travelType DROP DEFAULT")
            op.execute("ALTER TABLE trips ALTER COLUMN passengerCount DROP DEFAULT")
            op.execute("ALTER TABLE trips ALTER COLUMN additionalInfo DROP DEFAULT")


def downgrade() -> None:
    with op.batch_alter_table("trips") as batch_op:
        try:
            batch_op.drop_column("additionalInfo")
        except Exception:
            pass
        try:
            batch_op.drop_column("passengerCount")
        except Exception:
            pass
        try:
            batch_op.drop_column("travelType")
        except Exception:
            pass
