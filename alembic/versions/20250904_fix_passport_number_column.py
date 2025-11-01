"""
fix passportnumber column name to passportNumber

Revision ID: rev_250904_fix_passport
Revises: rev_250904_fix_passengers
Create Date: 2025-09-04 21:02:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "rev_250904_fix_passport"
down_revision = "rev_250904_fix_passengers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename passportnumber to passportNumber
    with op.batch_alter_table("passengers") as batch_op:
        batch_op.alter_column("passportnumber", new_column_name="passportNumber")


def downgrade() -> None:
    # Revert passportNumber back to passportnumber
    with op.batch_alter_table("passengers") as batch_op:
        batch_op.alter_column("passportNumber", new_column_name="passportnumber")
