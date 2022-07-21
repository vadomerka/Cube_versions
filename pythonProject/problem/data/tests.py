import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase

tests_to_lesson = sqlalchemy.Table(
    'tests_to_lessons',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('tests', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('tests.id')),
    sqlalchemy.Column('lessons', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('lessons.id'))
)


class Tests(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'tests'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    check_side = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    ans_side = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)


class TestsToUsers(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'TestsToUsers'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    test_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('tests.id'))
    lesson_id = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey('lessons.id'))
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('users.id'))
    best_result = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    last_result = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
