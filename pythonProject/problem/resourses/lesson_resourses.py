from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.lessons import Lessons, lessons_to_course
from data.courses import Courses
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
        # print([item.to_dict(only=('id', 'name')) for item in list(course.lessons)])  # .to_dict(only=('id', 'name'))
        ret = {'lesson': lesson.to_dict(only=('id', 'name'))}
        ret["lesson"]["words"] = \
            [item.to_dict(only=('id', 'hieroglyph', "translation")) for item in list(lesson.words)]
        ret["lesson"]["trainers"] = \
            [item.to_dict(only=('id', 'name')) for item in list(lesson.trainers)]
        ret["lesson"]["tests"] = \
            [item.to_dict(only=('id', 'name')) for item in list(lesson.tests)]
        # print(lesson.words)
        return jsonify(ret)

    def delete(self, lesson_id):
        abort_if_not_found(lesson_id)
        session = db_session.create_session()
        lesson = session.query(Lessons).get(lesson_id)
        session.delete(lesson)
        session.commit()
        return jsonify({'success': 'OK'})


# not working
class CourseLessonsResource(Resource):
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
