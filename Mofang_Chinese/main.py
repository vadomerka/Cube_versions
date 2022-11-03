from flask import Flask, render_template, redirect, url_for, flash
from flask import request, make_response, session, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from flask_mail import Mail, Message

# data base
from data import db_session
from data.words import Words, words_to_lesson, WordsToUsers
from data.lessons import Lessons, lessons_to_course
from data.courses import Courses, users_to_course
from data.users import User
from data.trainers import Trainers, TrainersToUsers
from data.tests import Tests, TestsToUsers

# flask forms
from forms.user import MakeUserForm, MakePasswordForm, LoginForm, ForgotPasswordForm, \
    ChangeProfileForm, ChangePasswordForm, ChangeDataForm, ChangeAuthorisedProfileForm
from forms.course import CoursesForm, AddItemToSomethingForm
from forms.lesson import LessonsForm, AddSomethingToLessonForm
from forms.word import WordsForm

# flask resourses
from resourses.course_resourses import CourseListResource, CourseResource
from resourses.dict_resourses import DictResourse, WordResourse, WordViewRecordingResource
from resourses.lesson_resourses import LessonResource, LessonListResource
from resourses.user_resourses import UserResource, UserListResource
from requests import get, post, delete, put
import requests
import json
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
app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'mofang_chinese_secret_key'
app.config['SECURITY_PASSWORD_SALT'] = 'mofang_chinese_secret_password_key'

# настройка почты
mail_settings = {
    "MAIL_SERVER": 'smtp.yandex.ru',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'pradomiri@yandex.ru',
    "MAIL_PASSWORD": 'lP!NIpDGGr6ADxE^N6ElWc1pX$8vq4@WU2w37LfnNWG$F2heXh'
}
app.config.update(mail_settings)
mail = Mail(app)

# настройка api
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


def pupil_js_list(array):
    array_js = []
    for i in range(len(array)):
        pupil = array[i]
        array_js.append(";".join([str(pupil.id), pupil.name, pupil.email, str(pupil.creator)]))
    array_js = ";;;".join(array_js)
    return array_js


def delete_extra_spaces(string):
    return " ".join(list(filter(lambda x: x, string.split())))


def generate_email_token(email):  # функция, создающая специальный токен
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_user_password_token(token, expiration=3600):
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


@app.route("/")
def index():  # основная страница, переадресация на курсы/словарь либо на страницу авторизации
    if current_user.is_authenticated:
        if current_user.courses:
            return redirect("/courses")
        return redirect("/dictionary")
    else:
        return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():  # страница авторизации пользователя
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
    if not current_user.is_authenticated:
        return render_template("unauthorized.html")
    if current_user.id == user_id:
        python_data = {
            "user_about": current_user.about
        }
        return render_template('profile.html', user=current_user, is_owner=1, python_data=python_data)
    profile_user = load_user(user_id)
    python_data = {
        "user_about": profile_user.about
    }
    return render_template('profile.html', user=profile_user, is_owner=0, python_data=python_data)


@app.route('/change_profile/<token>', methods=['GET', 'POST'])
def change_profile(token):  # первый вход ученика по ссылке
    db_sess = db_session.create_session()
    email = confirm_user_password_token(token)
    if not email:
        message = 'Ссылка для создания пароля недействительна или срок ее действия истек.'
        return render_template("wrong_link.html", message=message)
    user = db_sess.query(User).filter(User.email == email).first()
    if not user:
        return render_template("wrong_link.html")
    login_user(user)
    form = ChangeProfileForm()
    name_data = user.name
    if name_data is None:
        name_data = ""
    last_name_data = user.last_name
    if last_name_data is None:
        last_name_data = ""
    patronymic_data = user.patronymic
    if patronymic_data is None:
        patronymic_data = ""
    if user.about:
        python_data = {
            "about": user.about.split("\n")
        }
    else:
        python_data = {
            "about": [""]
        }
    email_data = user.email
    if current_user.hashed_password:
        form = ChangeAuthorisedProfileForm()
    if form.validate_on_submit():
        if current_user.hashed_password:
            # дополнительная проверка пароля нужна, чтобы учитель не мог изменять аккаунт, если ученик уже поставил пароль
            if not user.check_password(form.old_password.data):
                return render_template('change_profile.html',
                                       form=form,
                                       user=user,
                                       name_data=name_data,
                                       last_name_data=last_name_data,
                                       patronymic_data=patronymic_data,
                                       python_data=python_data,
                                       email_data=email_data,
                                       message="Неправильный пароль")
        if form.password.data != form.password_again.data:
            return render_template('change_profile.html',
                                   form=form,
                                   user=user,
                                   name_data=name_data,
                                   last_name_data=last_name_data,
                                   patronymic_data=patronymic_data,
                                   python_data=python_data,
                                   email_data=email_data,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)
        user.name = form.name.data
        user.last_name = form.last_name.data
        user.patronymic = form.patronymic.data
        user.about = form.about.data
        db_sess.add(user)
        user.set_password(form.password.data)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/')
    return render_template("change_profile.html", user=user, form=form, name_data=name_data,
                           last_name_data=last_name_data, patronymic_data=patronymic_data,
                           python_data=python_data, email_data=email_data)


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not current_user.is_authenticated:
        return render_template("unauthorized.html")
    form = ChangePasswordForm()
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
        db_sess.add(user)
        user.set_password(form.password.data)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/profile/' + str(current_user.id))
    return render_template("change_password.html", form=form)


@app.route('/change_data', methods=['GET', 'POST'])
@login_required
def change_data():
    if not current_user.is_authenticated:
        return render_template("unauthorized.html")
    user = load_user(current_user.id)
    name_data = user.name
    if name_data is None:
        name_data = ""
    last_name_data = user.last_name
    if last_name_data is None:
        last_name_data = ""
    patronymic_data = user.patronymic
    if patronymic_data is None:
        patronymic_data = ""
    if user.about:
        python_data = {
            "about": user.about.split("\n")
        }
    else:
        python_data = {
            "about": [""]
        }
    email_data = user.email

    form = ChangeDataForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)
        user.name = form.name.data
        user.last_name = form.last_name.data
        user.patronymic = form.patronymic.data
        user.about = form.about.data
        user.email = form.email.data
        db_sess.add(user)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/profile/' + str(current_user.id))
    return render_template("change_data.html", user=user, form=form, name_data=name_data,
                           last_name_data=last_name_data, patronymic_data=patronymic_data,
                           python_data=python_data, email_data=email_data)


def send_email(to, subject, template):  # функция отправки почты
    msg = Message(
        subject=subject,
        recipients=[to],
        html=template,
        sender=app.config.get("MAIL_USERNAME")
    )
    mail.send(msg)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_email_send():  # сценарий "пользователь забыл пароль"
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user_email = form.email.data  # пользователь вводит почту, на которую придет специальная ссылка
        with app.app_context():
            token = generate_email_token(user_email)  # создаем спец токен
            confirm_url = url_for('reset_password', token=token,
                                  _external=True)  # ссылка вида root/reset_password/<token>
            html = render_template('reset_password_letter.html',
                                   confirm_url=confirm_url)  # тело письма
            subject = "Сброс пароля Mofang Chinese"  # тема письма
            try:
                send_email(user_email, subject, html)  # отправление письма
            except Exception as e:
                print(str(e))
                return render_template("reset_password.html", form=form,
                                       message="не удалось отправить письмо, пожалуйста, повторите попытку позже")
        return redirect('/')
    return render_template("reset_password.html", form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):  # если пользователь получил ссылку для сброса пароля
    db_sess = db_session.create_session()
    email = confirm_user_password_token(token)
    if not email:
        message = 'Ссылка для восстановления пароля недействительна или срок ее действия истек.'
        return render_template("wrong_link.html", message=message)
    user = db_sess.query(User).filter(User.email == email).first()
    if not user:
        message = 'Пользователя с такой почтой не существует'
        return render_template("wrong_link.html", message=message)
    user.hashed_password = None
    logout_user()
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


@app.route('/pupils', methods=['GET', 'POST'])
@login_required
def pupils():
    all_users = get(root + '/rest_users').json()["users"]
    users_pupils = list(filter(lambda x: x["creator"] == current_user.id, all_users))
    items_js = {
        "all_items": users_pupils
    }
    return render_template('pupils.html', pupils=users_pupils, back_button_hidden="true",
                           items_js=items_js, max_items_number_on_one_page=60)


@app.route('/make_pupil', methods=['GET', 'POST'])
@login_required
def make_pupil():
    form = MakeUserForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('make_pupil.html',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            last_name=form.last_name.data,
            patronymic=form.patronymic.data,
            email=form.email.data,
            about=form.about.data,
            teacher=form.teacher.data,
            hints_enabled=1
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
    return render_template('make_pupil.html', back_button_hidden="false", back_url="/pupils",
                           form=form)


@app.route('/pupil/<int:pupil_id>/courses', methods=['GET', 'POST'])
@login_required
def pupil_courses_view(pupil_id):
    form = AddItemToSomethingForm()
    db_sess = db_session.create_session()
    pupil = db_sess.query(User).get(pupil_id)
    all_courses = []
    pupil_courses = []
    not_pupil_courses = []
    cur_user = db_sess.query(User).get(current_user.id)
    for course in cur_user.courses:
        course_js = {"id": course.id,
                     "name": course.name,
                     "about": course.about}
        all_courses.append(course_js)
        if course in pupil.courses:
            pupil_courses.append(course_js)
        else:
            not_pupil_courses.append(course_js)
    if form.validate_on_submit():
        courses_js = request.form.getlist('form-res')
        str_arr = courses_js[0]

        ans_arr = [int(item) for item in str_arr.split(",")]
        for course_js in all_courses:
            course = db_sess.query(Courses).get(course_js["id"])
            if ans_arr[course_js["id"]]:
                pupil.courses.append(course)
            else:
                if course in pupil.courses:
                    pupil.courses.remove(course)
        db_sess.merge(pupil)
        db_sess.commit()

        return redirect("/profile/" + str(pupil_id))
    all_items_js = json.dumps(all_courses)
    pupil_courses_js = json.dumps(pupil_courses)
    not_pupil_courses_js = json.dumps(not_pupil_courses)
    data_parser_file = open("static/data_parser.js", "w")
    data_parser_file.write(f"var all_items_js = {all_items_js}\n")
    data_parser_file.write(f"var pupil_courses_js = {pupil_courses_js}\n")
    data_parser_file.write(f"var not_pupil_courses_js = {not_pupil_courses_js}\n")
    data_parser_file.close()
    return render_template('pupil_courses.html',
                           back_button_hidden='false', back_url="/pupils",
                           items_in_column_number=13, column_number=4,
                           form=form)


@app.route('/generate_link/<int:user_id>', methods=['GET', 'POST'])
@login_required
def generate_link(user_id):
    user = load_user(user_id)
    return render_template("generate_link.html", user=user, root=root)


@app.route('/create_token_for_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def create_token_for_user(user_id):
    db_sess = db_session.create_session()
    user = load_user(user_id)
    token = generate_email_token(user.email)  # создаем спец токен на основе
    print(token)
    return {'token': str(token)}


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
        print(new_course.about)
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
    if course['about']:
        python_data = {
            "course_about": course['about'].split("\n")
        }
    else:
        python_data = {
            "course_about": []
        }
    course_name = course["name"]
    if not current_user.teacher:
        return render_template('course_view.html', course_data=course, back_button_hidden='false',
                               back_url="/courses",
                               current_user=current_user, course_name=course_name, course_about=course['about'],
                               python_data=python_data)
    form = CoursesForm()
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    course_name = course.name
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        course = db_sess.query(Courses).get(course_id)
        course.name = form.name.data
        course.about = form.about.data
        course_name = course.name
        if course['about']:
            python_data = {
                "course_about": course['about'].split("\n")
            }
        else:
            python_data = {
                "course_about": []
            }
        user = db_sess.query(User).get(current_user.id)
        user.courses.append(course)
        db_sess.merge(user)
        db_sess.commit()
        return render_template('course_view.html', course_data=course, back_button_hidden='false',
                               back_url="/courses", form=form,
                               current_user=current_user, course_name=course_name, python_data=python_data)
    return render_template('course_view.html', course_data=course, back_button_hidden='false',
                           back_url="/courses", form=form,
                           current_user=current_user, course_name=course_name, course_about=course.about.split("\r\n"),
                           python_data=python_data)


def lesson_learned(lesson_id, user_id):
    db_sess = db_session.create_session()
    user = load_user(user_id)
    lesson = db_sess.query(Lessons).get(lesson_id)
    if len(lesson.words) == 0:
        return 0, 0, 0
    lls = 0
    wls = 0
    for w in lesson.words:
        word_learn_state = db_sess.query(WordsToUsers).filter(WordsToUsers.users == user.id,
                                                              WordsToUsers.words == w.id).first().learn_state
        wls += word_learn_state / 2
    wls = int((wls / len(lesson.words)) * 100)
    test_results = db_sess.query(TestsToUsers).filter(TestsToUsers.lesson_id == lesson_id,
                                                      TestsToUsers.user_id == user.id).all()
    # print([t.id for t in test_results])
    tls = 0
    for t in test_results:
        tls += (t.best_result / len(lesson.words))
    tls = int((tls / len(lesson.tests)) * 100)
    # print(wls, tls)
    lls = int((wls + tls) / 2)
    return lls, wls, tls


@app.route('/course_statistics/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course_statistics(course_id):
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    json_course = get(root + '/rest_course/' + str(course_id)
                      ).json()
    json_course = json.dumps(course.about)
    data_parser_file = open("static/data_parser.js", "w")
    data_parser_file.write(f"var json_course_about = {json_course}\n")
    lessons_data = {}
    pupil_count = 0
    for lesson in course.lessons:
        lesson_percentage = 0
        completed_lesson = 0
        started_lesson = 0
        unstarted_lesson = 0
        for user in course.users:
            if not user.teacher:
                pupil_count += 1
                # lessson_learn_state, words_learn_state, tests_learn_state =
                res = lesson_learned(lesson.id, user.id)
                # lessons_data.append(res)
                lesson_percentage += res[0]
                if res[0] == 100:
                    completed_lesson += 1
                elif res[0] == 0:
                    unstarted_lesson += 1
                else:
                    started_lesson += 1
        lesson_percentage = int(lesson_percentage / pupil_count)
        lessons_data[lesson.id] = (lesson_percentage, completed_lesson, started_lesson, unstarted_lesson)
    return render_template("course_statistics.html", course=course, lessons_data=lessons_data,
                           len_course_lessons=len(course.lessons), len_course_pupils=pupil_count)  # ff


@app.route('/course/<int:course_id>/pupils', methods=['GET', 'POST'])
@login_required
def course_pupils_view(course_id):
    form = AddItemToSomethingForm()
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    all_pupils = []
    course_pupils = []
    not_course_pupils = []
    db_sess.query(User).all()
    for user in db_sess.query(User).all():
        if not user.teacher:
            all_pupils.append(user)
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
    course_pupils_js = pupil_js_list(course_pupils)
    not_course_pupils_js = pupil_js_list(not_course_pupils)
    return render_template('course_pupils.html', course=course, course_items=all_pupils,
                           back_button_hidden='false', back_url="/courses/" + str(course_id),
                           items_in_column_number=13, column_number=4, all_items_js=all_pupils_js,
                           # my_items_js=my_pupils_js, rest_items_js=rest_pupils_js,
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
    words_learn_states = {}
    for word in lesson["words"]:
        word_learn_state = db_sess.query(WordsToUsers).filter(WordsToUsers.users == current_user.id,
                                                              WordsToUsers.words == int(
                                                                  word["id"])).first().learn_state
        words_learn_states[word["id"]] = word_learn_state
    trainer_results = []
    for trainer in lesson["trainers"]:
        t_res = db_sess.query(TrainersToUsers).filter(
            TrainersToUsers.trainer_id == trainer["id"],
            TrainersToUsers.course_id == course_id,
            TrainersToUsers.lesson_id == lesson_id,
            TrainersToUsers.user_id == current_user.id).first()
        if t_res:
            trainer_results.append([trainer["id"], int(t_res.started), int(t_res.finished)])
        else:
            trainer_results.append([trainer["id"], 0, 0])

    test_results = db_sess.query(TestsToUsers).filter(TestsToUsers.course_id == course_id,
                                                      TestsToUsers.lesson_id == lesson_id,
                                                      TestsToUsers.user_id == current_user.id).all()
    test_results = [[res.test_id, res.id, res.last_result, res.best_result] for res in test_results]
    # print(test_results)
    lesson = db_sess.query(Lessons).get(lesson_id)
    lesson_name = lesson.name
    if current_user.teacher:
        form = LessonsForm()
        if form.validate_on_submit():
            lesson = db_sess.query(Lessons).get(lesson_id)
            current_course = db_sess.query(Courses).get(course_id)
            lesson.name = form.name.data
            lesson_name = lesson.name
            current_course.lessons.append(lesson)
            db_sess.merge(current_course)
            db_sess.commit()
            return render_template('lesson_view.html', lesson_data=lesson, course_id=course_id,
                                   back_button_hidden='false', back_url=f"/courses/{course_id}",
                                   lesson_words_js=lesson_words_js, column_number=column_number,
                                   items_in_column_number=items_in_column_number,
                                   test_results=test_results,
                                   trainer_results=trainer_results,
                                   len_test_results=len(test_results),
                                   words_learn_states=words_learn_states, form=form,
                                   lesson_name=lesson_name)
        return render_template('lesson_view.html', lesson_data=lesson, course_id=course_id,
                               back_button_hidden='false', back_url=f"/courses/{course_id}",
                               lesson_words_js=lesson_words_js, column_number=column_number,
                               items_in_column_number=items_in_column_number,
                               test_results=test_results,
                               trainer_results=trainer_results,
                               len_test_results=len(test_results),
                               words_learn_states=words_learn_states, form=form,
                               lesson_name=lesson_name)

    return render_template('lesson_view.html', lesson_data=lesson, course_id=course_id,
                           back_button_hidden='false', back_url=f"/courses/{course_id}",
                           lesson_words_js=lesson_words_js, column_number=column_number,
                           items_in_column_number=items_in_column_number, test_results=test_results,
                           trainer_results=trainer_results,
                           len_test_results=len(test_results),
                           words_learn_states=words_learn_states, lesson_name=lesson.name)


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


@app.route('/courses/<int:course_id>/lesson_statistics/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def lesson_statistics(course_id, lesson_id):
    db_sess = db_session.create_session()
    lesson = get(root + "/rest_lesson/" + str(lesson_id)).json()["lesson"]
    course = get(root + "/rest_course/" + str(course_id)).json()["course"]
    course_pupils = list(filter(lambda x: not x['teacher'], course["users"]))
    for i in range(len(course_pupils)):
        words_learned = 0
        words_viewed = 0
        trainers_completed = 0
        tests_completed = 0
        for w in lesson["words"]:
            w_learn_state = db_sess.query(WordsToUsers).filter(
                WordsToUsers.users == course_pupils[i]["id"],
                WordsToUsers.words == int(w["id"])).first().learn_state
            if w_learn_state == 1:
                words_viewed += 1
            elif w_learn_state == 2:
                words_learned += 1

        lesson_trainers = [(t.started, t.finished)
                           for t in db_sess.query(TrainersToUsers).filter(
                TrainersToUsers.user_id == course_pupils[i]["id"],
                TrainersToUsers.course_id == course_id,
                TrainersToUsers.lesson_id == lesson_id).all()]
        for t in lesson_trainers:
            if t[0] and t[1]:
                trainers_completed += 1

        lesson_tests = [(t.best_result, t.last_result)
                        for t in db_sess.query(TestsToUsers).filter(
                TestsToUsers.user_id == course_pupils[i]["id"],
                TestsToUsers.course_id == course_id,
                TestsToUsers.lesson_id == lesson_id).all()]
        for t in lesson_tests:
            if t[0] == len(lesson["words"]):
                tests_completed += 1

        course_pupils[i]["words_learned"] = words_learned
        course_pupils[i]["words_viewed"] = words_viewed
        course_pupils[i]["trainers_completed"] = trainers_completed
        course_pupils[i]["tests_completed"] = tests_completed
    json_course_pupils = json.dumps(course_pupils)
    data_parser_file = open("static/data_parser.js", "w")
    data_parser_file.write(f"var course_pupils = {json_course_pupils}\n")
    lesson_percentage = 0
    les = db_sess.query(Lessons).get(lesson_id)
    for user in db_sess.query(Courses).get(course_id).users:
        if not user.teacher:
            res = lesson_learned(les.id, user.id)[0]
            print(res)
            lesson_percentage += res
    return render_template("lesson_statistics.html", lesson_name=lesson["name"],
                           back_button_hidden='false', back_url=f"/courses/{course_id}",
                           lesson_words_len=len(lesson["words"]),
                           lesson_trainers_len=len(lesson["trainers"]),
                           lesson_tests_len=len(lesson["tests"]),
                           course_pupils=course_pupils, course_id=course_id, lesson_id=lesson_id,
                           lesson_percentage=lesson_percentage)


@app.route('/courses/<int:course_id>/lesson_statistics/<int:lesson_id>/pupil/<int:pupil_id>',
           methods=['GET', 'POST'])
@login_required
def lesson_pupil_statistics(course_id, lesson_id, pupil_id):
    db_sess = db_session.create_session()
    lesson = get(root + "/rest_lesson/" + str(lesson_id)).json()["lesson"]
    course = get(root + "/rest_course/" + str(course_id)).json()["course"]
    pupil = db_sess.query(User).get(pupil_id)
    words_learned = 0
    words_viewed = 0
    trainers_completed = 0
    trainers_uncompleted = 0
    tests_completed = 0
    tests_uncompleted = 0
    for w in lesson["words"]:
        w_learn_state = db_sess.query(WordsToUsers).filter(
            WordsToUsers.users == pupil.id,
            WordsToUsers.words == int(w["id"])).first().learn_state
        if w_learn_state == 1:
            words_viewed += 1
        elif w_learn_state == 2:
            words_learned += 1

    lesson_trainers = [(t.started, t.finished)
                       for t in db_sess.query(TrainersToUsers).filter(
            TrainersToUsers.user_id == pupil.id,
            TrainersToUsers.course_id == course_id,
            TrainersToUsers.lesson_id == lesson_id).all()]
    for t in lesson_trainers:
        if t[0] and t[1]:
            trainers_completed += 1
        else:
            trainers_uncompleted += 1

    lesson_tests = [(t.best_result, t.last_result)
                    for t in db_sess.query(TestsToUsers).filter(
            TestsToUsers.user_id == pupil.id,
            TestsToUsers.course_id == course_id,
            TestsToUsers.lesson_id == lesson_id).all()]
    for t in lesson_tests:
        if t[0] == len(lesson["words"]):
            tests_completed += 1
        else:
            tests_uncompleted += 1
    return render_template("lesson_pupil_statistics.html", pupil=pupil,
                           back_button_hidden='false',
                           back_url=f"/courses/{course_id}/lesson_statistics/{lesson_id}",
                           # lesson_words_len=lesson_words_len,
                           # lesson_trainers_len=lesson_trainers_len,
                           # lesson_tests_len=lesson_tests_len,
                           words_learned=words_learned,
                           words_viewed=words_viewed,
                           trainers_completed=trainers_completed,
                           trainers_uncompleted=trainers_uncompleted,
                           tests_completed=tests_completed,
                           tests_uncompleted=tests_uncompleted)


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
    items_js = {
        "my_items_js": my_words,
        "rest_items_js": rest_words,
        "all_items_js": all_words
    }
    max_words_number_on_one_page = 32
    return render_template("dictionary.html", all_words=all_words, current_user=current_user,
                           len_all_words=len_all_words,
                           my_words=my_words, rest_words=rest_words,
                           back_button_hidden="true", items_js=items_js,
                           max_items_number_on_one_page=max_words_number_on_one_page)


@app.route('/add_word', methods=['GET', 'POST'])
@login_required
def add_word():
    form = WordsForm()
    db_sess = db_session.create_session()
    image_start_preview = "/static/words_data/tutorial_down.png"
    all_words = get(root + "/rest_dict").json()["words"]
    json_all_words = json.dumps(all_words)
    data_parser_file = open("static/data_parser.js", "w")
    data_parser_file.write(f"var json_all_words = {json_all_words}\n")
    if form.validate_on_submit():
        new_word = Words()
        new_word.author = current_user.id
        new_word.hieroglyph = delete_extra_spaces(form.hieroglyph.data)
        new_word.translation = delete_extra_spaces(form.translation.data)
        new_word.transcription = delete_extra_spaces(form.transcription.data)
        new_word.phrase_ch = delete_extra_spaces(form.phrase_ch.data)
        new_word.phrase_ru = delete_extra_spaces(form.phrase_ru.data)
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
                           back_button_hidden="false", back_url="/dictionary",
                           all_words=all_words)


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
                           next_word_url="/dict_word/" + str(next_id),
                           words_learn_state=0,
                           hints_enabled=int(current_user.hints_enabled))


@app.route('/courses/<int:course_id>/lesson_word/<int:lesson_id>/word/<int:word_id>',
           methods=['GET', 'POST'])
@login_required
def lesson_word_view(course_id, lesson_id, word_id):
    db_sess = db_session.create_session()
    word = get(root + '/rest_word/' + str(word_id)).json()["word"]
    lesson = get(root + '/rest_lesson/' + str(lesson_id)
                 ).json()["lesson"]
    lesson_words = lesson["words"]
    ret = post(root + f"/rest_word_view_recording/{current_user.id}/{word_id}")
    # word_learn_state = db_sess.query(WordsToUsers).filter(WordsToUsers.words == word["id"] and
    #                                                       WordsToUsers.users == current_user.id)[0]
    words_learn_state = 1
    for w in lesson_words:
        word_learn_state = db_sess.query(WordsToUsers).filter(
            WordsToUsers.words == w["id"],
            WordsToUsers.users == current_user.id).first().learn_state
        if word_learn_state == 0:
            words_learn_state = 0
            break
    if len(lesson["trainers"]) != 0:
        first_trainer_id = lesson["trainers"][0]['id']
        # print(lesson["trainers"][0])
        trainer_href = f"/courses/{course_id}/lesson/{lesson_id}/trainer/{first_trainer_id}"
    else:
        trainer_href = ""
        words_learn_state = 0
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
                           words_learn_state=words_learn_state, trainer_href=trainer_href,
                           hints_enabled=int(current_user.hints_enabled))


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
                                  word.left_side_audio,
                                  str(word.id)]))
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
    les = get(root + '/rest_lesson/' + str(lesson_id)).json()
    lesson_trainers = les["lesson"]["trainers"]
    lesson_tests = les["lesson"]["tests"]
    is_last_trainer = False
    next_trainer_href = ""
    next_test_href = ""
    if lesson_trainers[-1]["id"] == trainer_id:
        is_last_trainer = True
        if len(lesson_tests) != 0:
            next_test_href = \
                f"/courses/{course_id}/lesson/{lesson_id}/test/{lesson_tests[0]['id']}"
    else:
        for i in range(len(lesson_trainers)):
            t = lesson_trainers[i]
            if t["id"] == trainer_id:
                next_trainer_href = \
                    f"/courses/{course_id}/lesson/{lesson_id}/trainer/{lesson_trainers[i + 1]['id']}"
                break

    all_words = db_sess.query(Words).all()

    lesson_words = db_list_to_javascript(lesson.words)
    lesson_all_words = db_list_to_javascript(all_words)

    prev_result = db_sess.query(TrainersToUsers).filter(TrainersToUsers.trainer_id == trainer_id,
                                                        TrainersToUsers.course_id == course_id,
                                                        TrainersToUsers.lesson_id == lesson_id,
                                                        TrainersToUsers.user_id == current_user.id).first()
    if prev_result:
        prev_result.started = 1
        db_sess.merge(prev_result)
    else:
        db_sess.add(TrainersToUsers(
            trainer_id=trainer_id,
            course_id=course_id,
            lesson_id=lesson_id,
            user_id=current_user.id,
            started=1,
            finished=0
        ))
    db_sess.commit()
    answer_button_number = 6
    return render_template('trainer_view.html', course=course, lesson=lesson, trainer=trainer,
                           lesson_words=lesson_words, answer_button_number=answer_button_number,
                           back_url=f"/courses/{course_id}/lesson/{lesson_id}",
                           back_button_hidden="false", all_words=lesson_all_words,
                           is_last_trainer=is_last_trainer, next_trainer_href=next_trainer_href,
                           next_test_href=next_test_href)


@app.route('/courses/<int:course_id>/lesson/<int:lesson_id>/trainer/<int:trainer_id>/result',
           methods=['GET', 'POST'])
@login_required
def trainer_result(course_id, lesson_id, trainer_id):
    db_sess = db_session.create_session()
    db_sess.query(TrainersToUsers).filter()
    prev_result = db_sess.query(TrainersToUsers).filter(TrainersToUsers.trainer_id == trainer_id,
                                                        TrainersToUsers.course_id == course_id,
                                                        TrainersToUsers.lesson_id == lesson_id,
                                                        TrainersToUsers.user_id == current_user.id).first()
    if prev_result:
        prev_result.finished = 1
        db_sess.merge(prev_result)
    else:
        db_sess.add(TrainersToUsers(
            trainer_id=trainer_id,
            course_id=course_id,
            lesson_id=lesson_id,
            user_id=current_user.id,
            started=1,
            finished=1
        ))
    db_sess.commit()
    return {'success': "OK"}


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
    les = get(root + '/rest_lesson/' + str(lesson_id)).json()
    lesson_tests = les["lesson"]["tests"]

    is_last_test = False
    next_test_href = ""
    # print(lesson_tests)
    if lesson_tests[-1]["id"] == test_id:
        is_last_test = True
    else:
        for i in range(len(lesson_tests)):
            t = lesson_tests[i]
            if t["id"] == test_id:
                next_test_href = \
                    f"/courses/{course_id}/lesson/{lesson_id}/test/{lesson_tests[i + 1]['id']}"
                # print(next_test_href)
                break

    answer_button_number = 6
    tests_list = []

    for i in range(len(lesson.words)):  # lesson_words - string, not list!
        rand_num = random.randint(0, len(all_tests) - 2)
        rand_test = all_tests[rand_num]
        tests_list.append(str(rand_test.check_side) + " " + str(rand_test.ans_side))
    tests_list = "  ".join(tests_list)
    if test.check_side == -1 and test.ans_side == -1:
        return render_template('ultimate_test_view.html', course=course, lesson=lesson, test=test,
                               lesson_words=lesson_words, answer_button_number=answer_button_number,
                               back_url=f"/courses/{course_id}/lesson/{lesson_id}",
                               back_button_hidden="false", all_words=lesson_all_words,
                               tests_list=tests_list, is_last_test=is_last_test,
                               next_test_href=next_test_href)
    return render_template('test_view.html', course=course, lesson=lesson, test=test,
                           lesson_words=lesson_words, answer_button_number=answer_button_number,
                           back_url=f"/courses/{course_id}/lesson/{lesson_id}",
                           back_button_hidden="false", all_words=lesson_all_words,
                           is_last_test=is_last_test, next_test_href=next_test_href)


@app.route('/courses/<int:course_id>/lesson/<int:lesson_id>/test/<int:test_id>/result',
           methods=['GET', 'POST'])
@login_required
def test_result(course_id, lesson_id, test_id):
    db_sess = db_session.create_session()
    results = request.json["results"].split(".")[:-1]
    words_id = request.json["words"].split(".")[:-1]
    right_answer_count = len(list(filter(lambda x: x, [bool(int(i)) for i in results])))
    prev_result = db_sess.query(TestsToUsers).filter(TestsToUsers.test_id == test_id,
                                                     TestsToUsers.course_id == course_id,
                                                     TestsToUsers.lesson_id == lesson_id,
                                                     TestsToUsers.user_id == current_user.id).first()
    for i in range(len(words_id)):
        word_learn_state = db_sess.query(WordsToUsers).filter(WordsToUsers.words == words_id[i],
                                                              WordsToUsers.users == current_user.id).first()
        if results[i] != '0':
            res = 2
        else:
            res = 1
        if word_learn_state:
            word_learn_state.learn_state = res
            db_sess.merge(word_learn_state)
        else:
            db_sess.add(WordsToUsers(
                words=words_id[0],
                users=current_user.id,
                learn_state=res
            ))
        db_sess.commit()
    if prev_result:
        prev_result = db_sess.query(TestsToUsers).get(prev_result.id)
        prev_result.last_result = right_answer_count
        prev_result.best_result = max(right_answer_count, prev_result.best_result)
        db_sess.merge(prev_result)
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
        new_word.hieroglyph = delete_extra_spaces(form.hieroglyph.data)
        new_word.translation = delete_extra_spaces(form.translation.data)
        new_word.transcription = delete_extra_spaces(form.transcription.data)
        new_word.phrase_ch = delete_extra_spaces(form.phrase_ch.data)
        new_word.phrase_ru = delete_extra_spaces(form.phrase_ru.data)
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
                           image_start_preview=image_start_preview,
                           all_words=all_words)


def main():
    db_session.global_init("db/users.db")
    app.run()


if __name__ == '__main__':
    main()
