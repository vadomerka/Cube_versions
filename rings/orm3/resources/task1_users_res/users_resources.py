from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify

from data import db_session
from data.users import User

from resources.task1_users_res.users_parser import parserAddUser
from datetime import datetime as dt

from werkzeug.security import generate_password_hash

def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


class UserResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict(
            only=('id', 'surname', 'name', 'age',
                  'position', 'speciality', 'address',
                  'email', 'modified_date'))})

    # def put(self, news_id):
    #     abort_if_news_not_found(news_id)
    #     args = parserEditNews.parse_args()
    #     session = db_session.create_session()
    #     news = session.query(News).get(news_id)
    #     if 'title' in args and args['title']:
    #         news.title = args['title']
    #     if 'content' in args and args['content']:
    #         news.content = args['content']
    #     if 'is_private' in args:
    #         news.is_private = args['is_private']
    #     session.commit()
    #     return jsonify({'news': news.to_dict(
    #         only=('title', 'content', 'user_id', 'is_private'))})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        session = db_session.create_session()
        news = session.query(User).all()
        return jsonify({'news': [item.to_dict(
            only=('title', 'content', 'user.name')) for item in news]})

    def post(self):
        args = parserAddUser.parse_args()
        session = db_session.create_session()
        if args['password'] != args['password_again']:
            abort(400, message="Passwords doesn't match")
        password = generate_password_hash(args['password'])
        user = User(
            'surname'=args["surname"],
            'name'=args["name"],
            'age'=args["age"],
            'position'=args["position"],
            'speciality'=args["speciality"],
            'address'=args["address"],
            'email'=args["email"],
            'password'=password,
            'modified_date'=dt.utcnow()
        )
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})
