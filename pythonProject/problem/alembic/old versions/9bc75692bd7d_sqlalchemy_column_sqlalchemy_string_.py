"""= sqlalchemy.Column(sqlalchemy.String, nullable=True)

Revision ID: 9bc75692bd7d
Revises: d36d85907d80
Create Date: 2022-06-20 11:48:47.446874

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9bc75692bd7d'
down_revision = 'd36d85907d80'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('patronymic', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'patronymic')
    # ### end Alembic commands ###
