"""
create trips table if missing and add any missing columns

Revision ID: 20240904_create_trips_if_missing
Revises: 20240904_update_trips_columns
Create Date: 2025-09-04 00:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240904_create_trips_if_missing"
down_revision = "20240904_update_trips_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    table_names = set(inspector.get_table_names())

    if "trips" not in table_names:
        op.create_table(
            "trips",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("airportName", sa.String(), nullable=False),
            sa.Column("travelDate", sa.String(), nullable=False),
            sa.Column("flightNumber", sa.String(), nullable=False),
            sa.Column("travelType", sa.String(), nullable=False),
            sa.Column(
                "passengerCount", sa.Integer(), nullable=False, server_default="0"
            ),
            sa.Column("additionalInfo", sa.String(), nullable=True, server_default=""),
        )
        # drop server defaults to match model
        op.execute('ALTER TABLE trips ALTER COLUMN "passengerCount" DROP DEFAULT')
        op.execute('ALTER TABLE trips ALTER COLUMN "additionalInfo" DROP DEFAULT')
    else:
        # ensure required columns exist (quoted names because of camelCase)
        existing_cols = {c["name"] for c in inspector.get_columns("trips")}
        add_ops = []
        if "airportName" not in existing_cols:
            add_ops.append(sa.Column("airportName", sa.String(), nullable=False))
        if "travelDate" not in existing_cols:
            add_ops.append(sa.Column("travelDate", sa.String(), nullable=False))
        if "flightNumber" not in existing_cols:
            add_ops.append(sa.Column("flightNumber", sa.String(), nullable=False))
        if "travelType" not in existing_cols:
            add_ops.append(sa.Column("travelType", sa.String(), nullable=False))
        if "passengerCount" not in existing_cols:
            add_ops.append(
                sa.Column(
                    "passengerCount", sa.Integer(), nullable=False, server_default="0"
                )
            )
        if "additionalInfo" not in existing_cols:
            add_ops.append(
                sa.Column(
                    "additionalInfo", sa.String(), nullable=True, server_default=""
                )
            )

        if add_ops:
            with op.batch_alter_table("trips") as batch_op:
                for col in add_ops:
                    batch_op.add_column(col)
            # drop server defaults if we added them
            if any(col.name == "passengerCount" for col in add_ops):
                op.execute(
                    'ALTER TABLE trips ALTER COLUMN "passengerCount" DROP DEFAULT'
                )
            if any(col.name == "additionalInfo" for col in add_ops):
                op.execute(
                    'ALTER TABLE trips ALTER COLUMN "additionalInfo" DROP DEFAULT'
                )


def downgrade() -> None:
    # We won't drop the table in downgrade to avoid data loss; noop.
    pass
