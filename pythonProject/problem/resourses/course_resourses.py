from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.courses import Courses, users_to_course
from data.users import User
from resourses.parser import parserAdd


def abort_if_news_not_found(course_id):
    session = db_session.create_session()
    course = session.query(Courses).get(course_id)
    if not course:
        abort(404, message=f"News {course_id} not found")


class CourseResource(Resource):
    def get(self, user_id, course_id):
        abort_if_news_not_found(course_id)
        session = db_session.create_session()
        course = session.query(Courses).get(course_id)
        # print([item.to_dict(only=('id', 'name')) for item in list(course.lessons)])  # .to_dict(only=('id', 'name'))
        ret = {'course': course.to_dict(only=('id', 'name', 'about'))}
        ret["course"]["lessons"] = [item.to_dict(only=('id', 'name')) for item in list(course.lessons)]
        return jsonify(ret)

    def delete(self, course_id):
        abort_if_news_not_found(course_id)
        session = db_session.create_session()
        course = session.query(Courses).get(course_id)
        session.delete(course)
        session.commit()
        return jsonify({'success': 'OK'})


class CourseListResource(Resource):
    def get(self, user_id):
        session = db_session.create_session()
        cur_user = session.query(User).filter(User.id == user_id).first()
        return jsonify({'courses': [item.to_dict(
            only=('id', 'name', 'about')) for item in cur_user.courses]})

    def post(self):
        args = parserAdd.parse_args()
        session = db_session.create_session()
        course = Courses(
            id=args['id'],
            name=args['name'],
            about=args['about'],
            author=args["author"]
        )
        session.add(course)
        session.commit()
        return jsonify({'success': 'OK'})
