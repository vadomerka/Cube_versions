from flask import Flask, render_template, redirect
from flask import request, make_response, session, abort

from data import db_session
from data.words import Words, words_to_lesson
from data.lessons import Lessons, lessons_to_course
from data.courses import Courses, users_to_course
from data.users import User

from forms.user import RegisterForm, LoginForm
from forms.course import CoursesForm
from forms.lesson import LessonsForm
from forms.word import WordsForm
import datetime as dt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from resourses.course_resourses import CourseListResource, CourseResource
from resourses.dict_resourses import DictResourse
from flask_restful import Api
from requests import get, post, delete, put
import os

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api.add_resource(CourseListResource, '/rest_courses/<int:user_id>')
api.add_resource(CourseResource, '/rest_courses/<int:user_id>/<int:course_id>')
api.add_resource(DictResourse, "/rest_dict")
login_manager = LoginManager()
login_manager.init_app(app)


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect("/courses")
    else:
        return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    # print(form.validate_on_submit())
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        return redirect('/courses')
    return render_template('register.html', title='Регистрация', form=form)


# response = requests.get('https://pythonexamples.org/', params=params)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    # print(get('http://localhost:5000/rest_courses/' + str(current_user.id)).json())
    user_courses = get('http://localhost:5000/rest_courses/' + str(current_user.id)).json()[
        "courses"]
    # print(user_courses)
    return render_template('courses.html', courses=user_courses, new_id=len(user_courses) + 1)


@app.route('/make_course', methods=['GET', 'POST'])
@login_required
def make_course():
    form = CoursesForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        new_course = Courses()
        # new_course.id = course_id
        new_course.name = form.name.data
        new_course.about = form.about.data
        current_user.courses.append(new_course)
        # print(current_user)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/courses')
    return render_template('make_course.html', form=form)


@app.route('/make_lesson/<int:course_id>', methods=['GET', 'POST'])
@login_required
def make_lesson(course_id):
    form = LessonsForm()
    db_sess = db_session.create_session()
    current_course = db_sess.query(Courses).get(course_id)
    all_words = db_sess.query(Words).all()
    if form.validate_on_submit():
        # print(form)  <forms.lesson.LessonsForm object at 0x7fd4defc9940>
        # print(form.words)
        new_lesson = Lessons()
        new_lesson.name = form.name.data
        # print(request.form.getlist('checks'))
        current_course.lessons.append(new_lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(course_id))
    return render_template('make_lesson.html', form=form, dictionary=all_words)


@app.route('/courses/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course_view(course_id):
    course = get('http://localhost:5000/rest_courses/' + str(current_user.id) + "/" + str(course_id)
                 ).json()["course"]
    return render_template('course_change.html', course_data=course)


@app.route('/dictionary', methods=['GET', 'POST'])
@login_required
def dict_view():
    all_words = get("http://localhost:5000/rest_dict").json()["words"]
    return render_template("dictionary.html", all_words=all_words, current_user=current_user)


@app.route('/add_word', methods=['GET', 'POST'])
@login_required
def add_word():
    form = WordsForm()
    db_sess = db_session.create_session()
    all_words = db_sess.query(Words).all()
    if form.validate_on_submit():
        new_word = Words()
        new_word.author = current_user.id
        new_word.hieroglyph = form.hieroglyph.data
        new_word.translation = form.translation.data
        front = request.files['front']
        left = request.files['left']
        right = request.files['right']
        up = request.files['up']
        down = request.files['down']
        path_to_file = os.path.dirname(__file__)
        full_path = os.path.join(path_to_file)
        filepath = os.path.join(full_path, "db", "dictionary", new_word.translation)
        if front:
            front.save(filepath + "_front.png")
            new_word.front_side = filepath + "_front.png"
        if left:
            left.save(filepath + "_left.png")
            new_word.left_side = filepath + "_left.png"
        if right:
            right.save(filepath + "_right.png")
            new_word.right_side = filepath + "_right.png"
        if up:
            up.save(filepath + "_up.png")
            new_word.up_side = filepath + "_up.png"
        if down:
            down.save(filepath + "_down.png")
            new_word.down_side = filepath + "_down.png"
        current_user.words.append(new_word)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/dictionary')
    return render_template('make_word.html', form=form, dictionary=all_words, filename="tmp")


def main():
    db_session.global_init("db/users.db")
    app.run()


if __name__ == '__main__':
    main()
"""
from flask import Flask
from flask import request, url_for, redirect
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gJ9c96Tz6sI5wzeb420x1zIdu7ZCx5BYmLZfBDHn'


@app.route('/sample_file_upload', methods=['POST', 'GET'])
def sample_file_upload():
    if request.method == 'GET':
        return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
     <link rel="stylesheet"
     href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta1/dist/css/bootstrap.min.css"
     integrity="sha384-giJF6kkoqNQ00vy+HMDP7azOuL0xtbfIcaT9wjKHr8RbDVddVHyTfAAsrekwKmP1"
     crossorigin="anonymous">
    <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
    <title>Пример загрузки файла</title>
  </head>
  <body>
    <h1>Загрузить файл</h1>

    <form method="post" enctype="multipart/form-data">
       <div class="form-group">
            <label for="photo">Выберите файл</label>
            <input type="file" class="form-control-file" id="photo" name="file">
            <img src="{url_for('static', filename='imgs/temp')}"
                    width="300" height="300">
        </div>
        <button type="submit" class="btn btn-primary">Отправить</button>
    </form>

  </body>
</html>'''
    elif request.method == 'POST':
        file = request.files['file']
        if file:
            path_to_file = os.path.dirname(__file__)
            full_path = os.path.join(path_to_file, "static", "imgs")
            file.save(os.path.join(full_path, "temp"))
            return redirect("/sample_file_upload")


if __name__ == '__main__':
    app.run(port=5000, host='127.0.0.1')
"""
