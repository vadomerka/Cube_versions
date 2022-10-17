from flask import Flask, render_template, redirect, url_for, flash
from flask import request, make_response, session, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from flask_mail import Mail, Message

# tables
from data import db_session
from data.words import Words, words_to_lesson, WordsToUsers
from data.lessons import Lessons, lessons_to_course
from data.courses import Courses, users_to_course
from data.users import User
from data.trainers import Trainers, TrainersToUsers
from data.tests import Tests, TestsToUsers

# forms
from forms.user import MakeUserForm, MakePasswordForm, LoginForm, ForgotPasswordForm, \
    NamePasswordForm, ChangeProfileForm
from forms.course import CoursesForm, AddUsersToCourseForm
from forms.lesson import LessonsForm, AddSomethingToLessonForm
from forms.word import WordsForm

# resourses
from resourses.course_resourses import CourseListResource, CourseResource
from resourses.dict_resourses import DictResourse, WordResourse, WordViewRecordingResource
from resourses.lesson_resourses import LessonResource, LessonListResource
from resourses.user_resourses import UserResource, UserListResource
from requests import get, post, delete, put
import requests
import json
from sqlalchemy import insert, create_engine
import os
import datetime as dt
from PIL import Image
import vlc
from itsdangerous import URLSafeTimedSerializer
import logging
import random

logging.basicConfig(filename="log.txt", level=logging.DEBUG,
                    format="%(asctime)s %(message)s", filemode="w")
logging.debug("Logging test...")
logging.info("The program is working as expected")
logging.warning("The program may not function properly")
logging.error("The program encountered an error")
logging.critical("The program crashed")
engine = create_engine('sqlite:///db/users.db', echo=True, future=True)
app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'mofang_chinese_secret_key'
app.config['SECURITY_PASSWORD_SALT'] = 'mofang_chinese_secret_password_key'
mail_settings = {
    "MAIL_SERVER": 'smtp.yandex.ru',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'pradomiri@yandex.ru',
    "MAIL_PASSWORD": 'wsRuHhBwL2'
}

app.config.update(mail_settings)
mail = Mail(app)

api.add_resource(CourseListResource, '/rest_courses/<int:user_id>')
api.add_resource(CourseResource, '/rest_course/<int:course_id>')
api.add_resource(DictResourse, "/rest_dict")
api.add_resource(WordResourse, "/rest_word/<int:word_id>")
api.add_resource(LessonResource, "/rest_lesson/<int:lesson_id>")
api.add_resource(LessonListResource, "/rest_lessons/<int:lesson_id>")
api.add_resource(UserResource, "/rest_user/<int:user_id>")
api.add_resource(UserListResource, "/rest_users")
api.add_resource(WordViewRecordingResource, '/rest_word_view_recording/<int:user_id>/<int:word_id>')
login_manager = LoginManager()
login_manager.init_app(app)
root = "http://localhost:5000"


def list_to_javascript(array):
    array_js = []
    for i in range(len(array)):
        word = array[i]
        array_js.append(";".join([str(word["id"]),
                                  word["hieroglyph"],
                                  word["translation"],
                                  word["transcription"],  # иероглиф
                                  word["phrase_ch"],  # перевод
                                  word["phrase_ru"],  # транскрипция
                                  word["image"],  # картинка  # словосочетание
                                  word["front_side_audio"],
                                  word["up_side_audio"],
                                  word["left_side_audio"],
                                  str(word["author"])]))
    array_js = ";;;".join(array_js)
    return array_js


@app.route("/style_loader")
def style_loader():
    return


@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.courses:
            return redirect("/courses")
        return redirect("/dictionary")
    else:
        return redirect('/login')


@app.route('/profile_change/<hash_token>', methods=['GET', 'POST'])
def profile_change(hash_token):
    db_sess = db_session.create_session()
    hash_token = int(hash_token)
    user = db_sess.query(User).filter(User.hash_token == hash_token).first()
    if user:
        login_user(user)
        return redirect("/change_password/" + str(user.id))
    return render_template("wrong_link.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(meta={'locales': ['ru']})
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.hashed_password and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        elif user and user.hashed_password and not user.check_password(form.password.data):
            return render_template('login.html',
                                   message="Неправильный пароль",
                                   form=form)
        return render_template('login.html',
                               message="Пользователя с такой почтой не существует",
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


@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def user_profile(user_id):
    db_sess = db_session.create_session()
    if current_user.id == user_id:
        return render_template('profile.html', user=current_user, is_owner=1)
    profile_user = db_sess.query(User).get(user_id)
    return render_template('profile.html', user=profile_user, is_owner=0)


@app.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    name_data = user.name
    last_name_data = user.last_name
    patronymic_data = user.patronymic
    about_data = user.about
    form = NamePasswordForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('change_password.html',
                                   form=form,
                                   user=user,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(user_id)
        user.name = form.name.data
        user.last_name = form.last_name.data
        user.patronymic = form.patronymic.data
        user.about = form.about.data

        db_sess.add(user)
        user.set_password(form.password.data)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/')
    return render_template("change_password.html", user=user, form=form, name_data=name_data,
                           last_name_data=last_name_data, patronymic_data=patronymic_data,
                           about_data=about_data)


@app.route('/change_profile', methods=['GET', 'POST'])
@login_required
def change_profile():
    # db_sess = db_session.create_session()
    user = current_user
    name_data = user.name
    last_name_data = user.last_name
    patronymic_data = user.patronymic
    about_data = user.about
    email_data = user.email
    form = ChangeProfileForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)
        if not user.check_password(form.old_password.data):
            return render_template('change_password.html',
                                   form=form,
                                   user=user,
                                   message="Неправильный пароль")
        if form.password.data != form.password_again.data:
            return render_template('change_password.html',
                                   form=form,
                                   user=user,
                                   message="Пароли не совпадают")
        user.name = form.name.data
        user.last_name = form.last_name.data
        user.patronymic = form.patronymic.data
        user.about = form.about.data
        user.email = form.email.data

        db_sess.add(user)
        user.set_password(form.password.data)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/')
    return render_template("change_password.html", user=user, form=form, name_data=name_data,
                           last_name_data=last_name_data, patronymic_data=patronymic_data,
                           about_data=about_data, email_data=email_data)


def send_email(to, subject, template):
    msg = Message(
        subject=subject,
        recipients=[to],
        html=template,
        sender=app.config.get("MAIL_USERNAME")
    )
    mail.send(msg)


def generate_reset_password_token(email):  # функция, создающая специальный токен
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_email_send():  # сценарий "пользователь забыл пароль"
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user_email = form.email.data  # пользователь вводит почту, на которую придет специальная ссылка
        with app.app_context():
            token = generate_reset_password_token(user_email)  # создаем спец токен на основе
            confirm_url = url_for('reset_password', token=token,
                                  _external=True)  # ссылка вида root/reset_password/<token>
            html = render_template('activate.html', confirm_url=confirm_url)  # тело письма
            subject = "Сброс пароля Mofang Chinese"  # тема письма
            send_email(user_email, subject, html)  # отправление письма
        return redirect('/')
    return render_template("reset_password.html", form=form)


def confirm_reset_password_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(  # расшифровываем, если не прошло определенное время
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        return email
    except:
        return False


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):  # если пользователь получил ссылку для сброса пароля
    db_sess = db_session.create_session()
    email = confirm_reset_password_token(token)
    if not email:
        message = 'Ссылка для восстановления пароля недействительна или срок ее действия истек.'
        return render_template("make_password.html", message=message, user=None, form=None)
    user = db_sess.query(User).filter(User.email == email).first()
    if not user:
        message = 'Пользователя с такой почтой не существует'
        return render_template("make_password.html", message=message, user=None, form=None)
    user.hashed_password = None
    login_user(user)
    form = MakePasswordForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('make_password.html',
                                   form=form,
                                   user=user,
                                   message="Пароли не совпадают",
                                   forgot_password=True)
        db_sess = db_session.create_session()
        user.set_password(form.password.data)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/')
    return render_template("make_password.html", user=user, form=form)


def pupil_js_list(array):
    array_js = []
    for i in range(len(array)):
        pupil = array[i]
        array_js.append(";".join([str(pupil.id), pupil.name, pupil.email, str(pupil.creator)]))
    array_js = ";;;".join(array_js)
    return array_js


@app.route('/pupils', methods=['GET', 'POST'])
@login_required
def pupils():
    db_sess = db_session.create_session()
    users_pupils = []
    all_users = db_sess.query(User).all()
    for user in all_users:
        if user.creator == current_user.id:
            one_user = get(root + "/rest_user/" + str(user.id)).json()["user"]
            user_courses = get(root + '/rest_courses/' + str(current_user.id)).json()
            user_courses = user.courses
            users_pupils.append(user)

    users_pupils_js = pupil_js_list(users_pupils)
    return render_template('pupils.html', pupils=users_pupils, back_button_hidden="true",
                           users_pupils_js=users_pupils_js, items_in_column_number=13,
                           column_number=4)


@app.route('/add_pupil', methods=['GET', 'POST'])
@login_required
def add_pupil():
    form = MakeUserForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('add_pupil.html',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            last_name=form.last_name.data,
            patronymic=form.patronymic.data,
            email=form.email.data,
            about=form.about.data,
            teacher=form.teacher.data
        )
        user.creator = current_user.id
        db_sess.add(user)
        for word in db_sess.query(Words).all():
            db_sess.add(WordsToUsers(
                words=word.id,
                users=user.id,
                learn_state=0
            ))
        db_sess.commit()
        return redirect('/generate_link/' + str(user.id))
    return render_template('add_pupil.html', back_button_hidden="false", back_url="/pupils",
                           form=form)


@app.route('/generate_link/<int:user_id>', methods=['GET', 'POST'])
@login_required
def generate_link(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    user.hash_token = 1
    return render_template("generate_link.html", user=user, root=root)


@app.route('/add_token_to_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def add_token_to_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    hash_token = hash(str(user_id) + " " + str(dt.datetime.now()))
    user.hash_token = hash_token
    db_sess.merge(user)
    db_sess.commit()
    return {'hash_token': str(hash_token)}


@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    ret = delete(root + "/rest_user/" + str(user_id)).json()
    if ret == {'success': 'OK'}:
        return redirect("/")
    else:
        return ret


@app.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    user_courses = get(root + '/rest_courses/' + str(current_user.id)).json()[
        "courses"]
    return render_template('courses.html', courses=user_courses, new_id=len(user_courses) + 1,
                           back_button_hidden='true', back_url='/dictionary')


@app.route('/make_course', methods=['GET', 'POST'])
@login_required
def make_course():
    form = CoursesForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        new_course = Courses()
        new_course.name = form.name.data
        new_course.about = form.about.data
        current_user.courses.append(new_course)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/courses')
    return render_template('make_course.html', form=form, function="Добавить курс",
                           back_button_hidden='false', back_url="/courses")


@app.route('/courses_delete/<int:course_id>', methods=['GET', 'POST'])
@login_required
def delete_course(course_id):
    ret = delete(root + "/rest_course/" + str(course_id)).json()
    if ret == {'success': 'OK'}:
        return redirect("/courses")
    else:
        # print("Couldn't delete course " + str(course_id))
        return redirect("/courses")


@app.route('/courses/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course_view(course_id):
    course = get(root + '/rest_course/' + str(course_id)
                 ).json()["course"]
    json_course = get(root + '/rest_course/' + str(course_id)
                      ).json()
    json_course = json.dumps(json_course['course']['about'])
    data_parser_file = open("static/data_parser.js", "w")
    data_parser_file.write(f"var json_course_about = {json_course}\n")
    return render_template('course_view.html', course_data=course, back_button_hidden='false',
                           back_url="/courses", json_course=json_course)


@app.route('/course/<int:course_id>/pupils', methods=['GET', 'POST'])
@login_required
def course_pupils_view(course_id):
    form = AddUsersToCourseForm()
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    all_pupils = []
    course_pupils = []
    not_course_pupils = []
    my_pupils = []
    rest_pupils = []
    db_sess.query(User).all()
    for user in db_sess.query(User).all():
        if not user.teacher:
            all_pupils.append(user)
            if user.creator == current_user.id:
                my_pupils.append(user)
            else:
                rest_pupils.append(user)
            if user in course.users:
                course_pupils.append(user)
            else:
                not_course_pupils.append(user)
    if form.validate_on_submit():
        pupils_js = request.form.getlist('form-res')
        str_arr = pupils_js[0]

        ans_arr = [int(item) for item in str_arr.split(",")]
        for pupil_js in all_pupils:
            if ans_arr[pupil_js.id]:
                pupil = db_sess.query(User).get(int(pupil_js.id))
                pupil.courses.append(course)
                db_sess.merge(pupil)
            else:
                pupil = db_sess.query(User).get(int(pupil_js.id))
                if course in pupil.courses:
                    pupil.courses.remove(course)

                db_sess.merge(pupil)
        db_sess.commit()

        return redirect("/courses/" + str(course_id))
    all_pupils_js = pupil_js_list(all_pupils)
    my_pupils_js = pupil_js_list(my_pupils)
    rest_pupils_js = pupil_js_list(rest_pupils)
    course_pupils_js = pupil_js_list(course_pupils)
    not_course_pupils_js = pupil_js_list(not_course_pupils)
    return render_template('course_pupils.html', course=course, course_items=all_pupils,
                           back_button_hidden='false', back_url="/courses/" + str(course_id),
                           items_in_column_number=13, column_number=4, all_items_js=all_pupils_js,
                           my_items_js=my_pupils_js, rest_items_js=rest_pupils_js,
                           course_items_js=course_pupils_js,
                           not_course_items_js=not_course_pupils_js,
                           form=form)


def lesson_words_js_list(array):
    array_js = []
    for i in range(len(array)):
        word = array[i]
        array_js.append(";".join([str(word['id']), word['hieroglyph'], word['translation']]))
    array_js = ";;;".join(array_js)
    return array_js


@app.route('/courses/<int:course_id>/lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def lesson_view(course_id, lesson_id):
    lesson = get(root + '/rest_lesson/' + str(lesson_id)
                 ).json()["lesson"]
    db_sess = db_session.create_session()

    column_number = 1
    items_in_column_number = 13
    if not current_user.teacher:
        items_in_column_number = 26
    lesson_words_js = lesson_words_js_list(lesson['words'])
    test_results = db_sess.query(TestsToUsers).filter(TestsToUsers.course_id == course_id,
                                                      TestsToUsers.lesson_id == lesson_id,
                                                      TestsToUsers.user_id == current_user.id).all()
    test_results = [[res.test_id, res.id, res.last_result, res.best_result] for res in test_results]
    return render_template('lesson_view.html', lesson_data=lesson, course_id=course_id,
                           back_button_hidden='false', back_url=f"/courses/{course_id}",
                           lesson_words_js=lesson_words_js, column_number=column_number,
                           items_in_column_number=items_in_column_number, test_results=test_results,
                           len_test_results=len(test_results))


@app.route('/make_lesson/<int:course_id>', methods=['GET', 'POST'])
@login_required
def make_lesson(course_id):
    form = LessonsForm()
    db_sess = db_session.create_session()
    current_course = db_sess.query(Courses).get(course_id)
    all_trainers = db_sess.query(Trainers).all()
    all_tests = db_sess.query(Tests).all()
    if form.validate_on_submit():
        new_lesson = Lessons()
        new_lesson.name = form.name.data
        words = request.form.getlist('lesson_word')
        for word_id in list(words):
            sql_word = db_sess.query(Words).get(int(word_id))
            new_lesson.words.append(sql_word)
        trainers = request.form.getlist('lesson_trainer')
        for trainers_id in list(trainers):
            sql_trainers = db_sess.query(Trainers).get(int(trainers_id))
            new_lesson.trainers.append(sql_trainers)
        tests = request.form.getlist('lesson_test')
        for tests_id in list(tests):
            sql_test = db_sess.query(Tests).get(int(tests_id))
            new_lesson.tests.append(sql_test)
        current_course.lessons.append(new_lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(course_id))
    return render_template('make_lesson.html', form=form,
                           trainers=all_trainers, tests=all_tests,
                           len_trainers=len(all_trainers), len_tests=len(all_tests))


@app.route('/add_trainers_to_lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def add_trainers_to_lesson(lesson_id):
    form = AddSomethingToLessonForm()
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    current_course = 0
    for c in db_sess.query(User).get(current_user.id).courses:
        if lesson in c.lessons:
            current_course = c
    all_trainers = db_sess.query(Trainers).all()
    lesson_trainers = lesson.trainers
    unused_trainers = sorted(list(set(all_trainers).difference(set(lesson.trainers))),
                             key=lambda x: x.id)

    if form.validate_on_submit():
        trainers = request.form.getlist('lesson_trainer')
        lesson.trainers = []
        for trainers_id in list(trainers):
            sql_trainers = db_sess.query(Trainers).get(int(trainers_id))
            lesson.trainers.append(sql_trainers)

        current_course.lessons.append(lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(current_course.id) + '/lesson/' + str(lesson_id))
    return render_template('add_trainers_to_lesson.html', trainers=all_trainers, form=form,
                           len_trainers=len(all_trainers),
                           lesson_trainers=lesson_trainers, unused_trainers=unused_trainers)


@app.route('/add_tests_to_lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def add_tests_to_lesson(lesson_id):
    form = AddSomethingToLessonForm()
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    current_course = 0
    for c in db_sess.query(User).get(current_user.id).courses:
        if lesson in c.lessons:
            current_course = c
    all_tests = db_sess.query(Tests).all()
    lesson_tests = lesson.tests
    unused_tests = sorted(list(set(all_tests).difference(set(lesson.tests))),
                          key=lambda x: x.id)

    if form.validate_on_submit():
        tests = request.form.getlist('lesson_test')
        lesson.tests = []
        for tests_id in list(tests):
            sql_tests = db_sess.query(Tests).get(int(tests_id))
            lesson.tests.append(sql_tests)

        current_course.lessons.append(lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(current_course.id) + '/lesson/' + str(lesson_id))
    return render_template('add_tests_to_lesson.html', tests=all_tests, form=form,
                           len_tests=len(all_tests),
                           lesson_tests=lesson_tests, unused_tests=unused_tests)


def add_words_js_list(array):
    array_js = []
    for i in range(len(array)):
        word = array[i]
        array_js.append(";".join([str(word.id), word.hieroglyph, word.translation]))
    array_js = ";;;".join(array_js)
    return array_js


@app.route('/add_words_to_lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def add_words_to_lesson(lesson_id):
    form = AddSomethingToLessonForm()
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    current_course = 0
    course_words = set()
    for c in db_sess.query(User).get(current_user.id).courses:
        if lesson in c.lessons:
            current_course = c
        for les in c.lessons:
            if les != lesson:
                for word in les.words:
                    course_words.add(word)

    all_words = db_sess.query(Words).all()
    my_words = []
    rest_words = []
    for word in all_words:
        if word.author == current_user.id:
            my_words.append(word)
        else:
            rest_words.append(word)
    lesson_words = lesson.words
    unused_words = sorted(list(set(all_words).difference(set(lesson_words))), key=lambda x: x.id)
    course_words = sorted(list(course_words), key=lambda x: x.id)
    not_course_words = sorted(list(set(all_words).difference(set(course_words))), key=lambda x: x.id)

    all_words_js = add_words_js_list(all_words)
    my_words_js = add_words_js_list(my_words)
    rest_words_js = add_words_js_list(rest_words)
    lesson_words_js = add_words_js_list(lesson_words)
    unused_words_js = add_words_js_list(unused_words)
    course_words_js = add_words_js_list(course_words)
    not_course_words_js = add_words_js_list(not_course_words)
    if form.validate_on_submit():
        items_js = request.form.getlist('form-res')
        str_arr = items_js[0]

        ans_arr = [int(item) for item in str_arr.split(",")]

        removed_word = False
        for i in range(len(ans_arr)):
            word = db_sess.query(Words).get(i)
            if ans_arr[i] == 0:
                if word and word in lesson.words:
                    lesson.words.remove(word)
                    removed_word = True
            else:
                lesson.words.append(word)
        if removed_word:
            test_results = db_sess.query(TestsToUsers).filter(
                TestsToUsers.course_id == current_course.id,
                TestsToUsers.lesson_id == lesson_id,
                TestsToUsers.user_id == current_user.id).all()
            for test in test_results:
                db_sess.delete(test)
        current_course.lessons.append(lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(current_course.id) + '/lesson/' + str(lesson_id))
    return render_template('add_words_to_lesson.html', lesson_words=lesson_words,
                           unused_words=unused_words,
                           dictionary=all_words, form=form, len_dictionary=len(all_words),
                           course_words=course_words, items_in_column_number=13, column_number=4,
                           all_items_js=all_words_js, my_items_js=my_words_js,
                           rest_items_js=rest_words_js, lesson_items_js=lesson_words_js,
                           unused_items_js=unused_words_js, course_items_js=course_words_js,
                           not_course_items_js=not_course_words_js)


@app.route('/change_lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def change_lesson(lesson_id):
    form = LessonsForm()
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    current_course = 0
    for c in db_sess.query(User).get(current_user.id).courses:
        if lesson in c.lessons:
            current_course = c

    if request.method == "GET":
        form.name.data = lesson.name

    if form.validate_on_submit():
        lesson.name = form.name.data
        current_course.lessons.append(lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(current_course.id) + '/lesson/' + str(lesson_id))

    return render_template('change_lesson_name.html', form=form)


@app.route('/courses/<int:course_id>/lesson_delete/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def delete_lesson(course_id, lesson_id):
    ret = delete(root + "/rest_lesson/" + str(lesson_id)).json()
    if ret == {'success': 'OK'}:
        return redirect("/courses/" + str(course_id))
    else:
        return abort(404, message=f"Lesson {lesson_id} not found")


@app.route("/delete_word_from_lesson/<int:lesson_id>/<int:word_id>", methods=['GET'])
@login_required
def delete_word_from_lesson(lesson_id, word_id):
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    word = db_sess.query(Words).get(word_id)
    if word in lesson.words:
        current_course = 0
        for c in db_sess.query(User).get(current_user.id).courses:
            if lesson in c.lessons:
                current_course = c
        lesson.words.remove(word)
        test_results = db_sess.query(TestsToUsers).filter(
            TestsToUsers.course_id == current_course.id,
            TestsToUsers.lesson_id == lesson_id,
            TestsToUsers.user_id == current_user.id).all()
        for test in test_results:
            db_sess.delete(test)
        db_sess.merge(lesson)
        db_sess.commit()

        return redirect('/courses/' + str(current_course.id) + "/lesson/" + str(lesson_id))
    return abort(404, message=f"Word {word_id} not found")


@app.route("/delete_trainer_from_lesson/<int:lesson_id>/<int:trainer_id>", methods=['GET'])
@login_required
def delete_trainer_from_lesson(lesson_id, trainer_id):
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    trainer = db_sess.query(Trainers).get(trainer_id)
    if trainer in lesson.trainers:
        lesson.trainers.remove(trainer)
        db_sess.merge(lesson)
        db_sess.commit()
        current_course = 0
        for c in db_sess.query(User).get(current_user.id).courses:
            if lesson in c.lessons:
                current_course = c
        return redirect('/courses/' + str(current_course.id) + "/lesson/" + str(lesson_id))
    return abort(404, message=f"Trainer {trainer_id} not found")


@app.route("/delete_test_from_lesson/<int:lesson_id>/<int:test_id>", methods=['GET'])
@login_required
def delete_test_from_lesson(lesson_id, test_id):
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    test = db_sess.query(Tests).get(test_id)
    if test in lesson.tests:
        lesson.tests.remove(test)
        db_sess.merge(lesson)
        db_sess.commit()
        current_course = 0
        for c in db_sess.query(User).get(current_user.id).courses:
            if lesson in c.lessons:
                current_course = c
        return redirect('/courses/' + str(current_course.id) + "/lesson/" + str(lesson_id))
    return abort(404, message=f"Test {test_id} not found")


@app.route("/delete_pupil_from_course/<int:course_id>/<int:pupil_id>", methods=['GET'])
@login_required
def delete_pupil_from_course(course_id, pupil_id):
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    pupil = db_sess.query(User).get(pupil_id)

    if pupil in course.users:
        course.users.remove(pupil)
        db_sess.merge(course)
        db_sess.commit()
        return redirect('/courses/' + str(course_id))

    return abort(404, message=f"Pupil {pupil_id} not found")


@app.route('/dictionary', methods=['GET', 'POST'])
@login_required
def dict_view():
    all_words = get(root + "/rest_dict").json()["words"]
    my_words = []
    rest_words = []
    for word in all_words:
        if word["author"] == current_user.id:
            my_words.append(word)
        else:
            rest_words.append(word)
    len_all_words = len(all_words)

    my_items_js = list_to_javascript(my_words)
    rest_items_js = list_to_javascript(rest_words)
    all_items_js = list_to_javascript(all_words)
    return render_template("dictionary.html", all_words=all_words, current_user=current_user,
                           len_all_words=len_all_words,
                           my_words=my_words, rest_words=rest_words,
                           my_items_js=my_items_js, rest_items_js=rest_items_js,
                           all_items_js=all_items_js, back_button_hidden="true",
                           column_number=2, items_in_column_number=15)


@app.route('/add_word', methods=['GET', 'POST'])
@login_required
def add_word():
    form = WordsForm()
    db_sess = db_session.create_session()
    image_start_preview = "/static/words_data/tutorial_down.png"
    if form.validate_on_submit():
        new_word = Words()
        new_word.author = current_user.id
        new_word.hieroglyph = form.hieroglyph.data
        new_word.translation = form.translation.data
        new_word.transcription = form.transcription.data
        new_word.phrase_ch = form.phrase_ch.data
        new_word.phrase_ru = form.phrase_ru.data
        image = request.files['image']
        transcription_audio = request.files['transcription_audio']
        phrase_audio = request.files['phrase_audio']
        translation_audio = request.files['translation_audio']
        path_to_file = os.path.dirname(__file__)
        full_path = os.path.join(path_to_file)
        save_name = str(hash(
            str(new_word.author) + "_" + str(new_word.translation) + "_" + str(new_word.hieroglyph)))
        filepath = os.path.join(full_path, "static", "words_data", save_name)
        if image:
            image.save(filepath + "_image.png")
            new_word.image = save_name + "_image.png"
            # print(7, new_word.image)
        else:
            new_word.image = "undefined_image.png"

        if transcription_audio:
            transcription_audio.save(filepath + "_trans_audio.mp3")
            new_word.front_side_audio = save_name + "_trans_audio.mp3"
            new_word.right_side_audio = save_name + "_trans_audio.mp3"
        else:
            new_word.front_side_audio = "undefined_trans_audio.mp3"
            new_word.right_side_audio = "undefined_trans_audio.mp3"
        if phrase_audio:
            phrase_audio.save(filepath + "_phrase_audio.mp3")
            new_word.up_side_audio = save_name + "_phrase_audio.mp3"
            new_word.left_side_audio = save_name + "_phrase_audio.mp3"
        else:
            new_word.up_side_audio = "undefined_phrase_audio.mp3"
            new_word.left_side_audio = "undefined_phrase_audio.mp3"
        if translation_audio:
            translation_audio.save(filepath + "_translation_audio.mp3")
            new_word.down_side_audio = save_name + "_translation_audio.mp3"
        else:
            new_word.down_side_audio = "undefined_translation_audio.mp3"
        new_word.creation_time = dt.datetime.now()
        # print(new_word.creation_time)
        cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
        cur_user.words.append(new_word)
        for user in db_sess.query(User).all():
            db_sess.add(WordsToUsers(
                words=new_word.id,
                users=user.id,
                learn_state=0
            ))
        db_sess.commit()
        db_sess.close()
        return redirect('/dictionary')
    return render_template('make_word.html', form=form, filename="tmp",
                           image_start_preview=image_start_preview,
                           # left_start_preview=left_start_preview,
                           # right_start_preview=right_start_preview,
                           # up_start_preview=up_start_preview,
                           # down_start_preview=down_start_preview,
                           back_button_hidden="false", back_url="/dictionary")


@app.route('/delete_word/<int:word_id>', methods=['GET', 'POST'])
@login_required
def delete_word(word_id):
    ret = delete(root + "/rest_word/" + str(word_id)).json()

    if ret == {'success': 'OK'}:
        return redirect("/dictionary")
    else:
        return ret


@app.route('/dict_word/<int:word_id>', methods=['GET', 'POST'])
@login_required
def dict_word_view(word_id):
    word = get(root + '/rest_word/' + str(word_id)).json()["word"]
    all_words = get(root + "/rest_dict").json()["words"]
    prev_id = 1
    next_id = 1
    prev_button_visibility = "visible"
    next_button_visibility = "visible"
    for i in range(len(all_words)):
        if all_words[i]["id"] == word["id"]:
            if i - 1 <= -1:
                prev_button_visibility = "hidden"
            else:
                prev_id = all_words[i - 1]["id"]

            if i + 1 >= len(all_words):
                next_button_visibility = "hidden"
            else:
                next_id = all_words[i + 1]["id"]
            break
    # print(url_for("user_data", filename=word["front_side"]))  # not working  ???
    db_sess = db_session.create_session()
    # print(db_sess.query(Words).get(word["id"]).hieroglyph, db_sess.query(Words).get(word["id"]).user)
    return render_template('word_view.html',
                           hieroglyph=word["hieroglyph"],
                           translation=word["translation"],
                           transcription=word["transcription"],
                           phrase_ch=word["phrase_ch"],
                           phrase_ru=word["phrase_ru"],
                           image_name=url_for("static", filename="words_data/" + word["image"]),
                           front_audio=url_for("static",
                                               filename="/words_data/" + word["front_side_audio"]),
                           left_audio=url_for("static",
                                              filename="/words_data/" + word["left_side_audio"]),
                           right_audio=url_for("static",
                                               filename="/words_data/" + word["right_side_audio"]),
                           up_audio=url_for("static",
                                            filename="/words_data/" + word["up_side_audio"]),
                           down_audio=url_for("static",
                                              filename="/words_data/" + word["down_side_audio"]),
                           back_url="/dictionary",
                           dict=all_words,
                           prev_button_visibility=prev_button_visibility,
                           next_button_visibility=next_button_visibility,
                           prev_word_url="/dict_word/" + str(prev_id),
                           next_word_url="/dict_word/" + str(next_id))


@app.route('/courses/<int:course_id>/lesson_word/<int:lesson_id>/word/<int:word_id>',
           methods=['GET', 'POST'])
@login_required
def lesson_word_view(course_id, lesson_id, word_id):
    db_sess = db_session.create_session()
    word = get(root + '/rest_word/' + str(word_id)).json()["word"]
    lesson_words = get(root + '/rest_lesson/' + str(lesson_id)
                       ).json()["lesson"]["words"]
    word_learn_state = db_sess.query(WordsToUsers).filter(WordsToUsers.words == word["id"] and
                                                          WordsToUsers.users == current_user.id)[0]
    # print(word_result.words, word_result.users, word_result.learn_state)
    prev_id = 1
    next_id = 1
    prev_button_visibility = "visible"
    next_button_visibility = "visible"
    for i in range(len(lesson_words)):
        if lesson_words[i]["id"] == word["id"]:
            if i - 1 <= -1:
                prev_button_visibility = "hidden"
            else:
                prev_id = lesson_words[i - 1]["id"]

            if i + 1 >= len(lesson_words):
                next_button_visibility = "hidden"
            else:
                next_id = lesson_words[i + 1]["id"]
            break
    ret = post(root + f"/rest_word_view_recording/{current_user.id}/{word_id}")
    return render_template('word_view.html',
                           hieroglyph=word["hieroglyph"],
                           translation=word["translation"],
                           transcription=word["transcription"],
                           phrase_ch=word["phrase_ch"],
                           phrase_ru=word["phrase_ru"],
                           image_name=url_for("static", filename="words_data/" + word["image"]),
                           front_audio=url_for("static",
                                               filename="/words_data/" + word["front_side_audio"]),
                           left_audio=url_for("static",
                                              filename="/words_data/" + word["left_side_audio"]),
                           right_audio=url_for("static",
                                               filename="/words_data/" + word["right_side_audio"]),
                           up_audio=url_for("static",
                                            filename="/words_data/" + word["up_side_audio"]),
                           down_audio=url_for("static",
                                              filename="/words_data/" + word["down_side_audio"]),
                           back_url="/courses/" + str(course_id) + "/lesson/" + str(lesson_id),
                           dict=lesson_words,
                           prev_button_visibility=prev_button_visibility,
                           next_button_visibility=next_button_visibility,
                           prev_word_url="/" + "courses/" + str(
                               course_id) + "/lesson_word/" + str(lesson_id) + "/word/" + str(
                               prev_id),
                           next_word_url="/" + "courses/" + str(
                               course_id) + "/lesson_word/" + str(lesson_id) + "/word/" + str(
                               next_id),
                           word_learn_state=word_learn_state)


def db_list_to_javascript(array):
    array_js = []
    for i in range(len(array)):
        word = array[i]
        array_js.append(";".join([word.hieroglyph,  # иероглиф
                                  word.translation,  # перевод
                                  word.transcription,  # транскрипция
                                  word.phrase_ch,  # картинка
                                  word.phrase_ru,  # свосочетание
                                  word.image,
                                  word.front_side_audio,
                                  word.up_side_audio,
                                  word.left_side_audio]))
    array_js = ";;;".join(array_js)
    return array_js


@app.route('/courses/<int:course_id>/lesson/<int:lesson_id>/trainer/<int:trainer_id>',
           methods=['GET', 'POST'])
@login_required
def lesson_trainer_view(course_id, lesson_id, trainer_id):
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    lesson = db_sess.query(Lessons).get(lesson_id)
    trainer = db_sess.query(Trainers).get(trainer_id)
    all_words = db_sess.query(Words).all()

    lesson_words = db_list_to_javascript(lesson.words)
    lesson_all_words = db_list_to_javascript(all_words)

    answer_button_number = 6
    return render_template('trainer_view.html', course=course, lesson=lesson, trainer=trainer,
                           lesson_words=lesson_words, answer_button_number=answer_button_number,
                           back_url=f"/courses/{course_id}/lesson/{lesson_id}",
                           back_button_hidden="false", all_words=lesson_all_words)


@app.route('/courses/<int:course_id>/lesson/<int:lesson_id>/test/<int:test_id>',
           methods=['GET', 'POST'])
@login_required
def lesson_test_view(course_id, lesson_id, test_id):
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    lesson = db_sess.query(Lessons).get(lesson_id)
    test = db_sess.query(Tests).get(test_id)
    all_tests = db_sess.query(Tests).all()
    all_words = db_sess.query(Words).all()

    lesson_words = db_list_to_javascript(lesson.words)
    lesson_all_words = db_list_to_javascript(all_words)

    answer_button_number = 6
    tests_list = []

    for i in range(len(lesson_words)):
        rand_test = all_tests[random.randint(0, len(all_tests) - 1)]
        tests_list.append(str(rand_test.check_side) + " " + str(rand_test.ans_side))
    tests_list = "  ".join(tests_list)
    if test.check_side == -1 and test.ans_side == -1:
        return render_template('ultimate_test.html', course=course, lesson=lesson, test=test,
                               lesson_words=lesson_words, answer_button_number=answer_button_number,
                               back_url=f"/courses/{course_id}/lesson/{lesson_id}",
                               back_button_hidden="false", all_words=lesson_all_words,
                               tests_list=tests_list)
    return render_template('test_view.html', course=course, lesson=lesson, test=test,
                           lesson_words=lesson_words, answer_button_number=answer_button_number,
                           back_url=f"/courses/{course_id}/lesson/{lesson_id}",
                           back_button_hidden="false", all_words=lesson_all_words)


@app.route('/courses/<int:course_id>/lesson/<int:lesson_id>/test/<int:test_id>/result',
           methods=['GET', 'POST'])
@login_required
def test_result(course_id, lesson_id, test_id):
    db_sess = db_session.create_session()

    results = request.json["results"].split(".")
    right_answer_count = len(list(filter(lambda x: x, [bool(int(i)) for i in results[:-1]])))
    prev_result = db_sess.query(TestsToUsers).filter(TestsToUsers.test_id == test_id,
                                                     TestsToUsers.course_id == course_id,
                                                     TestsToUsers.lesson_id == lesson_id,
                                                     TestsToUsers.user_id == current_user.id).first()
    if prev_result:
        prev_result.last_result = right_answer_count
        prev_result.best_result = max(right_answer_count, prev_result.best_result)
    else:
        db_sess.add(TestsToUsers(
            test_id=test_id,
            course_id=course_id,
            lesson_id=lesson_id,
            user_id=current_user.id,
            last_result=right_answer_count,
            best_result=right_answer_count
        ))
    db_sess.commit()
    return {'success': "OK"}


@app.route('/change_word/<int:word_id>', methods=['GET', 'POST'])
@login_required
def change_word(word_id):
    form = WordsForm()
    db_sess = db_session.create_session()
    all_words = db_sess.query(Words).all()
    new_word = db_sess.query(Words).get(word_id)
    path_to_file = os.path.dirname(__file__)
    full_path = os.path.join(path_to_file)

    prev_hieroglyph = new_word.hieroglyph
    prev_translation = new_word.translation
    prev_transcription = new_word.transcription
    prev_phrase_ch = new_word.phrase_ch
    prev_phrase_ru = new_word.phrase_ru

    image_file = Image.open(os.path.join(full_path, "static", "words_data", new_word.image))

    transcription_audio_file = vlc.MediaPlayer(os.path.join(
        full_path, "static", "words_data", new_word.front_side_audio))
    phrase_audio_file = vlc.MediaPlayer(
        os.path.join(full_path, "static", "words_data", new_word.up_side_audio))
    translation_audio_file = vlc.MediaPlayer(
        os.path.join(full_path, "static", "words_data", new_word.down_side_audio))

    if "undefined" not in new_word.front_side_audio:
        is_transcription_audio = "true"
    else:
        is_transcription_audio = "false"
    if "undefined" not in new_word.up_side_audio:
        is_phrase_audio = "true"
    else:
        is_phrase_audio = "false"
    if "undefined" not in new_word.down_side_audio:
        is_translation_audio = "true"
    else:
        is_translation_audio = "false"

    image_start_preview = "/static/words_data/" + new_word.image
    if form.validate_on_submit():
        new_word = db_sess.query(Words).get(word_id)
        new_word.author = current_user.id
        new_word.hieroglyph = form.hieroglyph.data
        new_word.translation = form.translation.data
        new_word.transcription = form.transcription.data
        new_word.phrase_ch = form.phrase_ch.data
        new_word.phrase_ru = form.phrase_ru.data
        image = request.files['image']
        transcription_audio = request.files['transcription_audio']
        phrase_audio = request.files['phrase_audio']
        translation_audio = request.files['translation_audio']
        path_to_file = os.path.dirname(__file__)
        full_path = os.path.join(path_to_file)
        save_name = str(hash(
            str(new_word.author) + "_" + str(new_word.translation) + "_" + str(new_word.hieroglyph)))
        filepath = os.path.join(full_path, "static", "words_data", save_name)
        if image:
            image.save(filepath + "_image.png")
            new_word.image = save_name + "_image.png"
        if transcription_audio:
            transcription_audio.save(filepath + "_trans_audio.mp3")
            new_word.front_side_audio = save_name + "_trans_audio.mp3"
            new_word.right_side_audio = save_name + "_trans_audio.mp3"
        if phrase_audio:
            phrase_audio.save(filepath + "_phrase_audio.mp3")
            new_word.up_side_audio = save_name + "_phrase_audio.mp3"
            new_word.left_side_audio = save_name + "_phrase_audio.mp3"
        if translation_audio:
            translation_audio.save(filepath + "_translation_audio.mp3")
            new_word.down_side_audio = save_name + "_translation_audio.mp3"

        new_word.creation_time = dt.datetime.now()
        cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
        cur_user.words.append(new_word)
        for user in db_sess.query(User).all():
            db_sess.add(WordsToUsers(
                words=new_word.id,
                users=user.id,
                learn_state=0
            ))
        db_sess.commit()
        db_sess.close()
        return redirect('/dictionary')
    return render_template('make_word.html', form=form, dictionary=all_words, filename="tmp",
                           prev_hieroglyph=prev_hieroglyph, prev_translation=prev_translation,
                           prev_transcription=prev_transcription, prev_phrase_ch=prev_phrase_ch,
                           prev_phrase_ru=prev_phrase_ru,
                           image_file=image_file,
                           transcription_audio_file=transcription_audio_file,
                           is_transcription_audio=is_transcription_audio,
                           phrase_audio_file=phrase_audio_file, is_phrase_audio=is_phrase_audio,
                           translation_audio_file=translation_audio_file,
                           is_translation_audio=is_translation_audio,
                           image_start_preview=image_start_preview)


def main():
    db_session.global_init("db/users.db")
    app.run()


if __name__ == '__main__':
    main()
