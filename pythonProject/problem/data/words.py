import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase

words_to_lesson = sqlalchemy.Table(
    'words_to_lessons',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('words', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('words.id')),
    sqlalchemy.Column('lessons', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('lessons.id'))
)


class Words(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'words'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    author = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True)

    user = orm.relation('User')
    # courses =
    hieroglyph = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    translation = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    front_side = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    left_side = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    right_side = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    up_side = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    down_side = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    front_side_audio = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    left_side_audio = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    right_side_audio = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    up_side_audio = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    down_side_audio = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    learn_state = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)


class WordsToUsers(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'WordsToUsers'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    words = sqlalchemy.Column(sqlalchemy.Integer,
                              sqlalchemy.ForeignKey('words.id'))
    users = sqlalchemy.Column(sqlalchemy.Integer,
                              sqlalchemy.ForeignKey('users.id'))
    learn_state = sqlalchemy.Column(sqlalchemy.Integer,
                                    nullable=True, default=0)
