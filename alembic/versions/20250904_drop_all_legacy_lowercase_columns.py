"""
drop all legacy lowercase columns from trips

Revision ID: rev_250904_drop_all_lower
Revises: rev_250904_drop_lower_trips
Create Date: 2025-09-04 20:58:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "rev_250904_drop_all_lower"
down_revision = "rev_250904_drop_lower_trips"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_cols = {c["name"] for c in inspector.get_columns("trips")}
    legacy_cols = {"traveltype", "passengercount", "additionalinfo"}
    cols_to_drop = legacy_cols & existing_cols

    if cols_to_drop:
        with op.batch_alter_table("trips") as batch_op:
            for col in cols_to_drop:
                batch_op.drop_column(col)


def downgrade() -> None:
    # Recreate legacy columns as nullable to avoid breaking old code, if any
    with op.batch_alter_table("trips") as batch_op:
        batch_op.add_column(sa.Column("traveltype", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("passengercount", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("additionalinfo", sa.String(), nullable=True))
