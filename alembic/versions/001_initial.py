"""initial

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create cars table
    op.create_table('cars',
                    sa.Column('car_id', sa.String(), nullable=False),
                    sa.Column('make', sa.String(), nullable=False),
                    sa.Column('model', sa.String(), nullable=False),
                    sa.Column('variant', sa.String(), nullable=True),
                    sa.Column('year', sa.Integer(),
                              nullable=False, index=True),
                    sa.Column('fuel_type', sa.String(),
                              nullable=False, index=True),
                    sa.Column('transmission', sa.String(), nullable=True),
                    sa.Column('km_driven', sa.Integer(), nullable=True),
                    sa.Column('price_onroad', sa.Integer(),
                              nullable=False, index=True),
                    sa.Column('city', sa.String(), nullable=False, index=True),
                    sa.Column('rto_state', sa.String(), nullable=True),
                    sa.Column('available', sa.Boolean(),
                              nullable=True, index=True),
                    sa.Column('inspection_score', sa.Float(), nullable=True),
                    sa.Column('warranty_months_left',
                              sa.Integer(), nullable=True),
                    sa.Column('resale_index', sa.Float(), nullable=True),
                    sa.Column('color', sa.String(), nullable=True),
                    sa.Column('owner_count', sa.Integer(), nullable=True),
                    sa.Column('insurance_valid_until',
                              sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(),
                              nullable=True, index=True),
                    sa.Column('inspection_summary',
                              postgresql.JSON(), nullable=True),
                    sa.PrimaryKeyConstraint('car_id')
                    )

    # Create test_drive_bookings table
    op.create_table('test_drive_bookings',
                    sa.Column('booking_id', sa.String(), nullable=False),
                    sa.Column('session_id', sa.String(),
                              nullable=True, index=True),
                    sa.Column('car_id', sa.String(),
                              nullable=True, index=True),
                    sa.Column('buyer_address', sa.Text(), nullable=True),
                    sa.Column('time_slot', sa.String(), nullable=True),
                    sa.Column('status', sa.String(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('booking_id')
                    )


def downgrade():
    op.drop_table('test_drive_bookings')
    op.drop_table('cars')
