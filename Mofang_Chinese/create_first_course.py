from data import db_session
from data.courses import Courses
from data.users import User
from data.trainers import Trainers
import datetime as dt


def create_first_course():
    db_session.global_init("db/users.db")
    session = db_session.create_session()

    new_course = Courses()
    new_course.name = "Новый курс"
    new_course.about = "Описание нового курса"
    teacher = session.query(User).filter(User.teacher == 1).all()[-1]
    teacher.courses.append(new_course)
    session.merge(teacher)
    session.commit()
