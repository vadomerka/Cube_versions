import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase

trainers_to_lesson = sqlalchemy.Table(
    'trainers_to_lessons',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('trainers', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('trainers.id')),
    sqlalchemy.Column('lessons', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('lessons.id'))
)


class Trainers(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'trainers'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    check_side = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    ans_side = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
