"""Initial migration

Revision ID: 380011c3703
Revises:
Create Date: 2015-11-03 16:41:50.171748

"""

# revision identifiers, used by Alembic.
revision = '380011c3703'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('people',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=200), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column(
            'favourite_pet', sa.Enum('cat', 'dog', 'other'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_people_name'), 'people', ['name'], unique=True)

    op.create_table('addresses',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('address', sa.Unicode(length=200), nullable=True),
        sa.Column('zip_code', sa.Unicode(length=20), nullable=True),
        sa.Column('city', sa.Unicode(length=100), nullable=True),
        sa.Column('country', sa.Unicode(length=3), nullable=True),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['person_id'], ['people.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('phone_numbers',
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('number', sa.String(length=40), nullable=True),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['person_id'], ['people.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('phone_numbers')
    op.drop_table('addresses')
    op.drop_index(op.f('ix_people_name'), table_name='people')
    op.drop_table('people')
