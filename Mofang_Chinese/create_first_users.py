from data import db_session
from data.users import User


def create_first_users():
    db_session.global_init("db/users.db")
    db_sess = db_session.create_session()
    new_user_email = "pradomiri@gmail.com"
    email_users = db_sess.query(User).filter(User.email == new_user_email).all()
    if email_users:
        print("user already exists")
        user = email_users[0]
        user.set_password("123456")
        user.teacher = 1
    else:
        user = User(
            name="teacher",
            email=new_user_email,
            teacher=1,
            hints_enabled=1,
        )
        user.set_password("123456")
    db_sess.merge(user)
    db_sess.commit()
    db_sess = db_session.create_session()
    teacher_id = db_sess.query(User).filter(User.teacher == 1).all()[-1].id
    new_user_email = "pupil@gmail.com"
    email_users = db_sess.query(User).filter(User.email == new_user_email).all()
    if email_users:
        print("user already exists")
        user = email_users[0]
        user.set_password("123456")
        user.teacher = 0
        user.creator = teacher_id
    else:
        user = User(
            name="pupil",
            email=new_user_email,
            teacher=0,
            hints_enabled=1,
            creator=teacher_id
        )
        user.set_password("123456")
    db_sess.merge(user)

    empty_user = User(creator=teacher_id)
    db_sess.merge(empty_user)
    db_sess.commit()


def create_one_user(name, email):
    db_session.global_init("db/users.db")
    db_sess = db_session.create_session()
    email_users = db_sess.query(User).filter(User.email == email).all()
    if email_users:
        print("user already exists")
        user = email_users[0]
        user.set_password("123456")
        user.teacher = 0
    else:
        user = User(
            name=name,
            email=email,
            teacher=0,
            hints_enabled=1,
        )
        user.set_password("123456")
    db_sess.merge(user)
    db_sess.commit()
