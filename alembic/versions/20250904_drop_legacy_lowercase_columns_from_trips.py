"""
drop legacy lowercase columns from trips

Revision ID: rev_250904_drop_lower_trips
Revises: 20240904_create_trips_if_missing
Create Date: 2025-09-04 18:35:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "rev_250904_drop_lower_trips"
down_revision = "20240904_create_trips_if_missing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_cols = {c["name"] for c in inspector.get_columns("trips")}
    legacy_cols = {"airportname", "traveldate", "flightnumber"}
    cols_to_drop = legacy_cols & existing_cols

    if cols_to_drop:
        with op.batch_alter_table("trips") as batch_op:
            for col in cols_to_drop:
                batch_op.drop_column(col)


def downgrade() -> None:
    # Recreate legacy columns as nullable to avoid breaking old code, if any
    with op.batch_alter_table("trips") as batch_op:
        batch_op.add_column(sa.Column("airportname", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("traveldate", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("flightnumber", sa.String(), nullable=True))
