from data import db_session
from data.users import User

db_session.global_init("db/users.db")
db_sess = db_session.create_session()
new_user_email = "pradomiri@gmail.com"
email_users = db_sess.query(User).filter(User.email == new_user_email).all()
if email_users:
    print("user already exists")
    user = email_users[0]
    user.set_password("1")
    print(user.hashed_password)
    user.teacher = 1
else:
    user = User(
        name="teacher",
        email=new_user_email,
        teacher=1
    )
    user.set_password("1")
db_sess.merge(user)
db_sess.commit()
