"""tests 3

Revision ID: 95822812d9d6
Revises: f34f448df7da
Create Date: 2022-07-19 10:35:31.844540

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95822812d9d6'
down_revision = 'f34f448df7da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('lessons_to_course')
    op.drop_table('trainers')
    op.drop_table('trainers_to_lessons')
    op.drop_table('courses')
    op.drop_table('tests')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.drop_table('users_to_course')
    op.drop_table('words_to_lessons')
    op.drop_table('words')
    op.drop_table('tests_to_lessons')
    op.drop_table('lessons')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lessons',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tests_to_lessons',
    sa.Column('tests', sa.INTEGER(), nullable=True),
    sa.Column('lessons', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['lessons'], ['lessons.id'], ),
    sa.ForeignKeyConstraint(['tests'], ['tests.id'], )
    )
    op.create_table('words',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('author', sa.INTEGER(), nullable=False),
    sa.Column('hieroglyph', sa.VARCHAR(), nullable=True),
    sa.Column('translation', sa.VARCHAR(), nullable=True),
    sa.Column('front_side', sa.VARCHAR(), nullable=True),
    sa.Column('left_side', sa.VARCHAR(), nullable=True),
    sa.Column('right_side', sa.VARCHAR(), nullable=True),
    sa.Column('up_side', sa.VARCHAR(), nullable=True),
    sa.Column('down_side', sa.VARCHAR(), nullable=True),
    sa.Column('front_side_audio', sa.VARCHAR(), nullable=True),
    sa.Column('right_side_audio', sa.VARCHAR(), nullable=True),
    sa.Column('up_side_audio', sa.VARCHAR(), nullable=True),
    sa.Column('left_side_audio', sa.VARCHAR(), nullable=True),
    sa.Column('down_side_audio', sa.VARCHAR(), nullable=True),
    sa.ForeignKeyConstraint(['author'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('words_to_lessons',
    sa.Column('words', sa.INTEGER(), nullable=True),
    sa.Column('lessons', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['lessons'], ['lessons.id'], ),
    sa.ForeignKeyConstraint(['words'], ['words.id'], )
    )
    op.create_table('users_to_course',
    sa.Column('users', sa.INTEGER(), nullable=True),
    sa.Column('courses', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['courses'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['users'], ['users.id'], )
    )
    op.create_table('users',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('email', sa.VARCHAR(), nullable=True),
    sa.Column('about', sa.VARCHAR(), nullable=True),
    sa.Column('hashed_password', sa.VARCHAR(), nullable=True),
    sa.Column('teacher', sa.BOOLEAN(), nullable=True),
    sa.Column('creator', sa.INTEGER(), nullable=True),
    sa.Column('last_name', sa.VARCHAR(), nullable=True),
    sa.Column('patronymic', sa.VARCHAR(), nullable=True),
    sa.Column('hash_token', sa.INTEGER(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_table('tests',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('check_side', sa.INTEGER(), nullable=True),
    sa.Column('ans_side', sa.INTEGER(), nullable=True),
    sa.Column('last_result', sa.INTEGER(), nullable=True),
    sa.Column('best_result', sa.INTEGER(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('courses',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('about', sa.VARCHAR(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('trainers_to_lessons',
    sa.Column('trainers', sa.INTEGER(), nullable=True),
    sa.Column('lessons', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['lessons'], ['lessons.id'], ),
    sa.ForeignKeyConstraint(['trainers'], ['trainers.id'], )
    )
    op.create_table('trainers',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('check_side', sa.INTEGER(), nullable=True),
    sa.Column('ans_side', sa.INTEGER(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lessons_to_course',
    sa.Column('lessons', sa.INTEGER(), nullable=True),
    sa.Column('courses', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['courses'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['lessons'], ['lessons.id'], )
    )
    # ### end Alembic commands ###
