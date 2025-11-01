"""
add orderId field to trips table

Revision ID: 20250918_add_orderid_to_trips
Revises: 20250918_add_flighttype_and_checks
Create Date: 2025-09-18 00:00:00.000000
"""

from alembic import op  # type: ignore
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250918_add_orderid_to_trips"
down_revision = "20250918_add_flighttype_and_checks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add orderId column
    with op.batch_alter_table("trips") as batch_op:
        try:
            batch_op.add_column(
                sa.Column("orderId", sa.String(), nullable=True, default=None)
            )
        except Exception:
            pass


def downgrade() -> None:
    # Drop orderId column
    with op.batch_alter_table("trips") as batch_op:
        try:
            batch_op.drop_column("orderId")
        except Exception:
            pass
