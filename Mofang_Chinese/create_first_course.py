from data import db_session
from data.courses import Courses
from data.users import User
from data.trainers import Trainers
from data.tests import Tests
from data.lessons import Lessons
from data.words import Words
import datetime as dt
from create_first_words import create_first_words


def create_first_course():
    db_session.global_init("db/users.db")
    session = db_session.create_session()

    new_course = Courses()
    new_course.name = "Новый курс"
    new_course.about = "Описание нового курса"
    teacher = session.query(User).filter(User.teacher == 1).all()[-1]

    empty_lesson = Lessons()
    new_course.lessons.append(empty_lesson)
    teacher.courses.append(new_course)

    empty_course = Courses()
    teacher.courses.append(empty_course)

    session.merge(teacher)
    session.commit()


def create_one_lesson():
    db_session.global_init("db/users.db")
    db_sess = db_session.create_session()
    new_lesson = Lessons()
    new_lesson.name = "Новый урок"
    courses = db_sess.query(Courses).all()
    if not courses:
        create_first_course()
        courses = db_sess.query(Courses).all()
    current_course = courses[0]
    trainers = [1, 2, 3]
    for trainers_id in trainers:
        sql_trainers = db_sess.query(Trainers).get(trainers_id)
        if sql_trainers:
            new_lesson.trainers.append(sql_trainers)
    tests = [1, 2, 3]
    for tests_id in tests:
        sql_test = db_sess.query(Tests).get(tests_id)
        if sql_test:
            new_lesson.tests.append(sql_test)
    all_words = db_sess.query(Words).all()
    if not all_words:
        create_first_words()
        all_words = db_sess.query(Words).all()
    words_list = all_words
    for w in words_list:
        new_lesson.words.append(w)
    current_course.lessons.append(new_lesson)
    db_sess.merge(current_course)
    db_sess.commit()


if __name__ == '__main__':
    create_first_course()
