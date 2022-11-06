from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.lessons import Lessons, lessons_to_course
from data.courses import Courses
from data.users import User
from resourses.parser import parserAdd


def abort_if_not_found(lesson_id):
    session = db_session.create_session()
    lesson = session.query(Lessons).get(lesson_id)
    if not lesson:
        abort(404, message="Object not found")


class LessonResource(Resource):
    def get(self, lesson_id):
        abort_if_not_found(lesson_id)
        session = db_session.create_session()
        lesson = session.query(Lessons).get(lesson_id)
        ret = {'lesson': lesson.to_dict(only=('id', 'name'))}
        ret["lesson"]["words"] = \
            [item.to_dict(only=('id', 'hieroglyph', "translation")) for item in list(lesson.words)]
        ret["lesson"]["trainers"] = \
            [item.to_dict(only=('id', 'name')) for item in list(lesson.trainers)]
        ret["lesson"]["tests"] = \
            [item.to_dict(only=('id', 'name')) for item in list(lesson.tests)]
        ret["lesson"]["course"] = \
            [item.to_dict(only=('id', 'name')) for item in list(lesson.courses)][0]
        # print(lesson.words)
        return jsonify(ret)

    def delete(self, lesson_id):
        abort_if_not_found(lesson_id)
        session = db_session.create_session()
        lesson = session.query(Lessons).get(lesson_id)
        session.delete(lesson)
        session.commit()
        return jsonify({'success': 'OK'})


class UserLessonListResource(Resource):
    def get(self, user_id):
        abort_if_not_found(user_id)
        session = db_session.create_session()
        cur_user = session.query(User).get(user_id)
        user_lessons = {"user_lessons": []}
        for c in cur_user.courses:
            for lesson in c.lessons:
                course_lesson = lesson.to_dict(only=('id', 'name'))
                course_lesson["words"] = [item.to_dict(only=('id', 'hieroglyph', "translation")) for item in list(lesson.words)]
                user_lessons["user_lessons"].append(course_lesson)
        return jsonify(user_lessons)


class LessonListResource(Resource):
    def get(self):
        session = db_session.create_session()
        ret = {"lessons": []}
        all_lessons = session.query(Lessons).all()
        for lesson in all_lessons:
            js_les = {lesson.to_dict(only=('id', 'name'))}
            js_les["words"] = [item.to_dict(only=('id', 'hieroglyph', "translation")) for item in list(lesson.words)]
            js_les["trainers"] = [item.to_dict(only=('id', 'name')) for item in list(lesson.trainers)]
            js_les["tests"] = [item.to_dict(only=('id', 'name')) for item in list(lesson.tests)]
            js_les["course"] = [item.to_dict(only=('id', 'name')) for item in list(lesson.courses)][0]
            ret["lessons"].append(js_les)
        return jsonify(ret)
