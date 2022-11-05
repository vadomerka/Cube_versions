from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.courses import Courses, users_to_course
from data.trainers import TrainersToUsers
from data.tests import TestsToUsers
from data.users import User
from resourses.parser import parserAdd
from flask import request


def abort_if_not_found(id):
    session = db_session.create_session()
    course = session.query(Courses).get(id)
    if not course:
        abort(404, message="Object not found", id=id)


class CourseResource(Resource):
    def get(self, course_id):
        abort_if_not_found(course_id)
        session = db_session.create_session()
        course = session.query(Courses).get(course_id)
        ret = {'course': course.to_dict(only=('id', 'name', 'about'))}
        ret["course"]["lessons"] = [item.to_dict(only=('id', 'name')) for item in
                                    list(course.lessons)]
        ret["course"]["users"] = [item.to_dict(only=('id', 'name', 'email', 'teacher')) for item in
                                  list(course.users)]
        return jsonify(ret)

    def delete(self, course_id):
        abort_if_not_found(course_id)
        session = db_session.create_session()
        for ttu in session.query(TrainersToUsers).filter(TrainersToUsers.course_id == course_id).all():
            session.delete(ttu)
        for ttu in session.query(TestsToUsers).filter(TestsToUsers.course_id == course_id).all():
            session.delete(ttu)
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
        if cur_user:
            return jsonify({'courses': [item.to_dict(
                only=('id', 'name', 'about')) for item in cur_user.courses]})
        return abort(404, message=f"User {user_id} not found")
