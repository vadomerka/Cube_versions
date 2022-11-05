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
        abort(404, message=f"lesson {lesson_id} not found")


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


class LessonListResource(Resource):
    def get(self, req, item_id):
        if req == "user_lessons":
            user_id = item_id
            session = db_session.create_session()
            cur_user = session.query(User).get(user_id)
            user_lessons = {"user_lessons": []}
            for c in cur_user.courses:
                for lesson in c.lessons:
                    course_lesson = lesson.to_dict(only=('id', 'name'))
                    course_lesson["words"] = [item.to_dict(only=('id', 'hieroglyph', "translation")) for item in list(lesson.words)]
                    user_lessons["user_lessons"].append(course_lesson)
            return jsonify(user_lessons)
        else:  # not working
            session = db_session.create_session()
            cur_user = session.query(User).filter(User.id == user_id).first()
            return jsonify({'courses': [item.to_dict(
                only=('id', 'name', 'about')) for item in cur_user.courses]})
