"""user creator

Revision ID: 6707621a75e4
Revises: b8f79f977286
Create Date: 2022-06-20 11:13:06.755802

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6707621a75e4'
down_revision = 'b8f79f977286'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('creaator', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'creaator')
    # ### end Alembic commands ###
