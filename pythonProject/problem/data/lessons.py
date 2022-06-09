import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase

lessons_to_course = sqlalchemy.Table(
    'lessons_to_course',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('lessons', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('lessons.id')),
    sqlalchemy.Column('courses', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('courses.id'))
)


class Lessons(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'lessons'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    words = orm.relation("Words",
                         secondary="words_to_lessons",
                         backref="lessons")
    trainers = orm.relation("Trainers",
                            secondary="trainers_to_lessons",
                            backref="lessons")
