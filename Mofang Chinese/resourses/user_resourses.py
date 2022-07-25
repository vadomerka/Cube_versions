from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.courses import Courses, users_to_course
from data.users import User
from resourses.parser import parserAdd
from flask import request


def abort_if_not_found(id):
    session = db_session.create_session()
    user = session.query(User).get(id)
    if not user:
        abort(404, message=f"User {id} not found")


class UserResource(Resource):
    def get(self, id):
        abort_if_not_found(id)
        session = db_session.create_session()
        user = session.query(User).get(id)
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
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        # print(users)
        ret = jsonify({'users': [item.to_dict(
            only=('id', 'email', 'name', 'about', 'hashed_password', 'teacher'))
            for item in users]})
        # print(ret)

        return ret

    def post(self, user_id):
        if not request.json:
            return jsonify({'error': 'Empty request'})
        elif not all(key in request.json for key in
                     ['name', 'about']):
            return jsonify({'error': 'Bad request'})
        args = parserAdd.parse_args()
        session = db_session.create_session()
        new_id = max([c.id for c in session.query(Courses)]) + 1
        course = Courses(
            id=new_id,
            name=args['name'],
            about=args['about']
        )
        session.add(course)
        session.commit()
        return jsonify({'success': 'OK'})
