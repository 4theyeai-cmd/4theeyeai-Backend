"""
fix passengers column names to camelCase

Revision ID: rev_250904_fix_passengers
Revises: rev_250904_drop_all_lower
Create Date: 2025-09-04 21:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "rev_250904_fix_passengers"
down_revision = "rev_250904_drop_all_lower"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename columns to match the model
    with op.batch_alter_table("passengers") as batch_op:
        batch_op.alter_column("lastname", new_column_name="lastName")
        batch_op.alter_column("nationalid", new_column_name="nationalId")
        batch_op.alter_column("luggagecount", new_column_name="luggageCount")
        batch_op.alter_column("passengertype", new_column_name="passengerType")


def downgrade() -> None:
    # Revert column names back to lowercase
    with op.batch_alter_table("passengers") as batch_op:
        batch_op.alter_column("lastName", new_column_name="lastname")
        batch_op.alter_column("nationalId", new_column_name="nationalid")
        batch_op.alter_column("luggageCount", new_column_name="luggagecount")
        batch_op.alter_column("passengerType", new_column_name="passengertype")
