"""
add nationality column to passengers table

Revision ID: rev_250105_add_nationality
Revises: rev_250904_fix_passengers
Create Date: 2025-01-05 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "rev_250105_add_nationality"
down_revision = "rev_250904_fix_passport"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nationality column to passengers table
    with op.batch_alter_table("passengers") as batch_op:
        batch_op.add_column(
            sa.Column(
                "nationality", sa.String(), nullable=True, server_default="ایرانی"
            )
        )


def downgrade() -> None:
    # Remove nationality column from passengers table
    with op.batch_alter_table("passengers") as batch_op:
        batch_op.drop_column("nationality")
