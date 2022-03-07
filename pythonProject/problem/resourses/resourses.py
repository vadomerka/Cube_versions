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
    def get(self, course_id):
        abort_if_news_not_found(course_id)
        session = db_session.create_session()
        course = session.query(Courses).get(course_id)
        print(course)
        return jsonify({'course': course.to_dict(
            only=('id', 'name', 'about'))})

    def delete(self, course_id):
        abort_if_news_not_found(course_id)
        session = db_session.create_session()
        course = session.query(Courses).get(course_id)
        session.delete(course)
        session.commit()
        return jsonify({'success': 'OK'})


class CourseListResource(Resource):
    def get(self):
        session = db_session.create_session()
        courses = session.query(Courses).all()
        print(courses[0])
        return jsonify({'courses': [item.to_dict(
            only=('id', 'name', 'about')) for item in courses]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        course = Courses(
            id=args['id'],
            name=args['name'],
            about=args['about']
        )
        session.add(course)
        session.commit()
        return jsonify({'success': 'OK'})
