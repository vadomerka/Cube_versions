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

    def __repr__(self):
        return f"<Course> {self.id}"

    # def to_dict(self, only=(), rules=(),
    #             date_format=None, datetime_format=None, time_format=None, tzinfo=None,
    #             decimal_format=None, serialize_types=None):
    #     super().to_dict(only, rules,
    #                     date_format, datetime_format, time_format, tzinfo, decimal_format,
    #                     serialize_types)
