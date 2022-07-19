from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.courses import Courses, users_to_course
from data.users import User
from resourses.parser import parserAdd
from flask import request


def abort_if_not_found(course_id):
    session = db_session.create_session()
    course = session.query(Courses).get(course_id)
    if not course:
        abort(404, message=f"Course {course_id} not found")


class CourseResource(Resource):
    def get(self, course_id):
        abort_if_not_found(course_id)
        session = db_session.create_session()
        course = session.query(Courses).get(course_id)
        ret = {'course': course.to_dict(only=('id', 'name', 'about'))}
        ret["course"]["lessons"] = [item.to_dict(only=('id', 'name')) for item in
                                    list(course.lessons)]
        ret["course"]["users"] = [item.to_dict(only=('id', 'name')) for item in
                                  list(course.users)]
        return jsonify(ret)

    def delete(self, course_id):
        abort_if_not_found(course_id)
        session = db_session.create_session()
        course = session.query(Courses).get(course_id)
        for lesson in course.lessons:
            session.delete(lesson)
        session.delete(course)
        session.commit()
        return jsonify({'success': 'OK'})


class CourseListResource(Resource):
    def get(self, user_id):
        session = db_session.create_session()
        cur_user = session.query(User).filter(User.id == user_id).first()
        return jsonify({'courses': [item.to_dict(
            only=('id', 'name', 'about')) for item in cur_user.courses]})

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
