import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase

users_to_course = sqlalchemy.Table(
    'users_to_course',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('users', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('courses', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('courses.id'))
)


class Courses(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'courses'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    # users = orm.relation("Users",
    #                        secondary="users_to_course",
    #                        backref="courses")
