from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.courses import Courses, users_to_course
from data.users import User
from data.words import Words, WordsToUsers
from resourses.parser import parserAdd
from flask import request


def abort_if_not_found(id):
    session = db_session.create_session()
    user = session.query(User).get(id)
    if not user:
        abort(404, message="Object not found", id=id)


class UserResource(Resource):
    def get(self, user_id):
        abort_if_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        ret = {'user': user.to_dict(only=('id',
                                          'name',
                                          'email',
                                          "about",
                                          "hashed_password",
                                          "teacher"))}
        ret["user"]["courses"] = [item.to_dict(only=('id', 'name', "about")) for item in
                                  list(user.courses)]
        ret["user"]["words"] = [item.to_dict(only=('id',
                                                   'hieroglyph',
                                                   "translation")) for item in
                                list(user.words)]
        return jsonify(ret)

    def delete(self, user_id):
        abort_if_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        words_to_this_user = session.query(WordsToUsers).filter(WordsToUsers.users == user_id).all()
        if words_to_this_user:
            for wtu in words_to_this_user:
                session.delete(wtu)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        ret = {"users": []}
        for user in users:
            u_item = user.to_dict(only=('id',
                                        'name',
                                        'email',
                                        "about",
                                        "hashed_password",
                                        "teacher",
                                        "creator"))
            u_item["courses"] = [item.to_dict(only=('id', 'name', "about")) for item in
                                 list(user.courses)]
            u_item["words"] = [item.to_dict(only=('id',
                                                  'hieroglyph',
                                                  "translation")) for item in
                               list(user.words)]
            ret["users"].append(u_item)
        return jsonify(ret)
