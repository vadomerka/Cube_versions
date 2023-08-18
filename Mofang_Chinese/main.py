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
from resourses.lesson_resourses import LessonResource, LessonListResource, UserLessonListResource
from resourses.user_resourses import UserResource, UserListResource
# from resourses.user_resourses import UserResource, UserListResource
from requests import get, post, delete, put
import requests
import json
import os
import datetime as dt
from PIL import Image
# import vlc
import wave
from pydub import AudioSegment
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
    "MAIL_PASSWORD": 'AMT45gkSn8HeumPa'
}
app.config.update(mail_settings)
mail = Mail(app)

# настройка api
api.add_resource(CourseListResource, '/rest_courses/<int:user_id>')
api.add_resource(CourseResource, '/rest_course/<int:course_id>')
api.add_resource(DictResourse, "/rest_dict")
api.add_resource(WordResourse, "/rest_word/<int:word_id>")
api.add_resource(LessonResource, "/rest_lesson/<int:lesson_id>")
api.add_resource(LessonListResource, "/rest_lessons")
api.add_resource(UserLessonListResource, "/rest_user_lessons/<int:user_id>")
api.add_resource(UserResource, "/rest_user/<int:user_id>")
api.add_resource(UserListResource, "/rest_users")
api.add_resource(WordViewRecordingResource, '/rest_word_view_recording/<int:user_id>/<int:word_id>')
login_manager = LoginManager()
login_manager.init_app(app)
# root = "http://mofang.ru"
root = "http://localhost:5000"

# создание базы данных
db_session.global_init("db/users.db")


# используется для удаления лишних пробелов в тексте при создании слова
def delete_extra_spaces(string):
    return " ".join(list(filter(lambda x: x, string.split())))


def generate_email_token(email):  # функция, создающая специальный токен
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_user_password_token(token, expiration=3600):  # расшифровка ключа в почту пользователя
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


def send_email(to, subject, template):  # функция отправки почты
    msg = Message(
        subject=subject,
        recipients=[to],
        html=template,
        sender=app.config.get("MAIL_USERNAME")
    )
    mail.send(msg)


def lesson_learned(lesson_id, user_id):  # подсчет статистики урока
    db_sess = db_session.create_session()
    user = load_user(user_id)
    lesson = db_sess.query(Lessons).get(lesson_id)
    if len(lesson.words) == 0:
        return 0, 0, 0
    wls = 0
    for w in lesson.words:
        word_learn_state = db_sess.query(WordsToUsers).filter(WordsToUsers.users == user.id,
                                                              WordsToUsers.words == w.id).first()
        if word_learn_state:
            word_learn_state = word_learn_state.learn_state
        if word_learn_state:
            wls += word_learn_state / 2
        else:
            wls += 0
    if len(lesson.trainers) == 0:
        wls = 0
    else:
        wls = int((wls / len(lesson.words)) * 100)
    test_results = db_sess.query(TestsToUsers).filter(TestsToUsers.lesson_id == lesson_id,
                                                      TestsToUsers.user_id == user.id).all()
    tls = 0
    for t in test_results:
        tls += (t.best_result / len(lesson.words))

    if len(lesson.tests) == 0:
        tls = 0
    else:
        tls = int((tls / len(lesson.tests)) * 100)
    lls = int((wls + tls) / 2)
    return lls, wls, tls


def t_word_to_javascript(array):  # перевод списка слов в список для просмотра тренажеров и тестов
    array_js = []
    for i in range(len(array)):
        word = array[i]
        array_js.append([word.hieroglyph,  # иероглиф
                         word.translation,  # перевод
                         word.transcription,  # транскрипция
                         word.phrase_ch,  # картинка
                         word.phrase_ru,  # свосочетание
                         word.image,
                         word.front_side_audio,
                         word.up_side_audio,
                         word.left_side_audio,
                         word.id])
    return array_js


@app.route("/")
def index():  # основная страница, переадресация на курсы/словарь либо на страницу авторизации
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)
        if user.courses:
            return redirect("/courses")
        return redirect("/dictionary")
    else:
        return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():  # страница авторизации пользователя
    if current_user.is_authenticated:
        logout_user()
    form = LoginForm(meta={'locales': ['ru']})
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.hashed_password and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        elif user and user.hashed_password and not user.check_password(form.password.data):
            return render_template('user_templates/login.html',
                                   message="Неправильный пароль",
                                   form=form, back_button_hidden="true", header_disabled="true")
        return render_template('user_templates/login.html',
                               message="Пользователя с такой почтой не существует",
                               form=form, back_button_hidden="true", header_disabled="true")
    return render_template('user_templates/login.html', title='Авторизация', form=form, back_button_hidden="true",
                           header_disabled="true")


@app.route('/logout')
def logout():  # выход из аккаунта пользователя
    if current_user.is_authenticated:
        logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):  # загрузка пользователя из базы данных
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def user_profile(user_id):  # просмотр профиля пользователя
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    profile_user = load_user(user_id)
    if not profile_user:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true",
                               object="Пользователь")
    is_owner = 0
    if current_user.id == user_id:
        is_owner = 1
    python_data = {"user_about": profile_user.about}
    return render_template('user_templates/profile.html', user=profile_user, is_owner=is_owner,
                           python_data=python_data, back_url="/pupils")


@app.route('/change_profile/<token>', methods=['GET', 'POST'])
def change_profile(token):  # первый вход ученика по ссылке
    db_sess = db_session.create_session()
    email = confirm_user_password_token(token)
    if not email:
        message = 'Ссылка для создания пароля недействительна или срок ее действия истек.'
        return render_template("error_templates/wrong_link.html", message=message, back_button_hidden="true")
    user = db_sess.query(User).filter(User.email == email).first()
    if not user:
        return render_template("error_templates/wrong_link.html", back_button_hidden="true")
    login_user(user)
    form = ChangeProfileForm()
    name_data = user.name
    last_name_data = user.last_name
    patronymic_data = user.patronymic
    if name_data is None:
        name_data = ""
    if last_name_data is None:
        last_name_data = ""
    if patronymic_data is None:
        patronymic_data = ""
    if user.about:
        python_data = {"about": user.about.split("\n")}
    else:
        python_data = {"about": [""]}
    email_data = user.email
    if current_user.hashed_password:
        form = ChangeAuthorisedProfileForm()
    if form.validate_on_submit():
        if current_user.hashed_password:
            # дополнительная проверка пароля нужна, чтобы учитель не мог изменять аккаунт, если ученик уже поставил пароль
            if not user.check_password(form.old_password.data):
                return render_template('user_templates/change_profile.html', form=form, user=user,
                                       name_data=name_data, last_name_data=last_name_data,
                                       patronymic_data=patronymic_data, python_data=python_data,
                                       email_data=email_data, header_disabled="true",
                                       message="Неправильный пароль")
        if form.password.data != form.password_again.data:
            return render_template('user_templates/change_profile.html', form=form, user=user, name_data=name_data,
                                   last_name_data=last_name_data, patronymic_data=patronymic_data,
                                   python_data=python_data, email_data=email_data,
                                   header_disabled="true", message="Пароли не совпадают")
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
    return render_template("user_templates/change_profile.html", user=user, form=form, name_data=name_data,
                           last_name_data=last_name_data, patronymic_data=patronymic_data,
                           python_data=python_data, email_data=email_data, header_disabled="true")


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():  # пользователь изменяет пароль
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    form = ChangePasswordForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)
        if not user.check_password(form.old_password.data):
            return render_template('user_templates/change_password.html',
                                   form=form,
                                   message="Неправильный пароль",
                                   back_url="/profile/" + str(current_user.id))
        if form.password.data != form.password_again.data:
            return render_template('user_templates/change_password.html',
                                   form=form,
                                   message="Пароли не совпадают",
                                   back_url="/profile/" + str(current_user.id))
        db_sess.add(user)
        user.set_password(form.password.data)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/profile/' + str(current_user.id))
    return render_template("user_templates/change_password.html", form=form,
                           back_url="/profile/" + str(current_user.id))


@app.route('/change_data', methods=['GET', 'POST'])
def change_data():  # пользователь изменяет свои данные
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    user = load_user(current_user.id)
    name_data = user.name
    last_name_data = user.last_name
    patronymic_data = user.patronymic
    email_data = user.email
    if name_data is None:
        name_data = ""
    if last_name_data is None:
        last_name_data = ""
    if patronymic_data is None:
        patronymic_data = ""
    if user.about:
        python_data = {"about": user.about.split("\n")}
    else:
        python_data = {"about": [""]}

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
    return render_template("user_templates/change_data.html", form=form, name_data=name_data,
                           last_name_data=last_name_data, patronymic_data=patronymic_data,
                           python_data=python_data, email_data=email_data,
                           back_url="/profile/" + str(current_user.id))


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_email_send():  # сценарий "пользователь забыл пароль"
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user_email = form.email.data  # пользователь вводит почту, на которую придет специальная ссылка
        with app.app_context():
            token = generate_email_token(user_email)  # создаем спец токен
            confirm_url = url_for('reset_password', token=token,
                                  _external=True,
                                  back_url="/")  # ссылка вида root/reset_password/<token>
            html = render_template('user_templates/reset_password_letter.html',
                                   confirm_url=confirm_url)  # тело письма
            subject = "Сброс пароля Mofang Chinese"  # тема письма
            try:
                send_email(user_email, subject, html)  # отправление письма
            except Exception as e:
                return render_template("user_templates/reset_password.html", form=form,
                                       message="Не удалось отправить письмо, пожалуйста, повторите попытку позже.",
                                       back_url="/")
        return redirect('/')
    return render_template("user_templates/reset_password.html", form=form, back_url="/")


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):  # если пользователь получил ссылку для сброса пароля
    db_sess = db_session.create_session()
    email = confirm_user_password_token(token)
    if not email:
        message = 'Ссылка для восстановления пароля недействительна или срок ее действия истек.'
        return render_template("error_templates/wrong_link.html", message=message, back_button_hidden="true")
    user = db_sess.query(User).filter(User.email == email).first()
    if not user:
        message = 'Пользователя с такой почтой не существует'
        return render_template("error_templates/wrong_link.html", message=message, back_button_hidden="true")
    user.hashed_password = None
    logout_user()
    form = MakePasswordForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('user_templates/make_password.html', form=form, back_button_hidden="true",
                                   message="Пароли не совпадают",
                                   forgot_password=True)
        db_sess = db_session.create_session()
        user.set_password(form.password.data)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/')
    return render_template("user_templates/make_password.html", form=form, back_button_hidden="true")


@app.route('/pupils', methods=['GET', 'POST'])
def pupils():  # список учеников учителя
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    all_users = get(root + '/rest_users').json()["users"]
    for i in range(len(all_users)):
        if not all_users[i]["name"]:
            all_users[i]["name"] = "Имя не указано"
        if not all_users[i]["email"]:
            all_users[i]["email"] = "Почта не указана"
    users_pupils = list(filter(lambda x: x["creator"] == current_user.id and not x["teacher"],
                               all_users))
    items_js = {"all_items": users_pupils}
    return render_template('user_templates/pupils.html', pupils=users_pupils, back_button_hidden="true",
                           items_js=items_js, max_items_number_on_one_page=60)


@app.route('/make_pupil', methods=['GET', 'POST'])
def make_pupil():  # создание нового пользователя
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    form = MakeUserForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('user_templates/make_pupil.html', form=form,
                                   message="Пользователь уже существует", back_url="/pupils")
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
    return render_template('user_templates/make_pupil.html', back_url="/pupils",
                           form=form)


@app.route('/generate_link/<int:user_id>', methods=['GET', 'POST'])
def generate_link(user_id):  # создает ссылку на вход для пользователя
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    user = load_user(user_id)
    if not user:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               object="Пользователь")
    if user.creator != current_user.id:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    return render_template("user_templates/generate_link.html", user=user, root=root)


@app.route('/pupil/<int:pupil_id>/courses', methods=['GET', 'POST'])
def pupil_courses_view(pupil_id):  # добавление курсов к ученику
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    cur_user_response = get(root + '/rest_user/' + str(current_user.id)).json()  # request
    if cur_user_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Пользователь")
    cur_user = cur_user_response["user"]
    pupil_response = get(root + '/rest_user/' + str(pupil_id)).json()  # request
    if pupil_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Пользователь")
    pupil = pupil_response["user"]
    if pupil_id == current_user.id:
        return redirect("/courses")
    if load_user(pupil_id).creator != current_user.id:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    if pupil_id == current_user.id:
        return redirect("/courses")

    form = AddItemToSomethingForm()
    all_items = cur_user["courses"]
    max_id = max([item["id"] for item in all_items])
    added_items = list(filter(lambda x: x in pupil["courses"], all_items))
    not_added_items = list(filter(lambda x: x not in pupil["courses"], all_items))
    items_js = {
        "all_items": all_items,
        "added_items": added_items,
        "not_added_items": not_added_items,
        "max_id": max_id
    }
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        courses_js = request.form.getlist('form-res')
        str_arr = courses_js[0]
        pupil = db_sess.query(User).get(pupil_id)
        ans_arr = [int(item) for item in str_arr.split(",")]
        for course_js in all_items:
            course = db_sess.query(Courses).get(course_js["id"])
            if ans_arr[course_js["id"]]:
                pupil.courses.append(course)
            else:
                if course in pupil.courses:
                    pupil.courses.remove(course)
        db_sess.merge(pupil)
        db_sess.commit()
        return redirect("/profile/" + str(pupil_id))
    return render_template('course_templates/pupil_courses.html',
                           back_url="/pupils",
                           max_items_number_on_one_page=60,
                           form=form, items_js=items_js)


@app.route('/create_token_for_user/<int:user_id>', methods=['GET', 'POST'])
# создание токена для спец ссылки (используется в user_templates/generate_link.html)
def create_token_for_user(user_id):
    if request.method == 'POST':
        user = load_user(user_id)
        token = generate_email_token(user.email)
        if not user:
            token = "user_not_found"
        return {'token': str(token)}
    else:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")


@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):  # удалить профиль пользователя
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if current_user.id != user_id:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    ret = delete(root + "/rest_user/" + str(user_id)).json()  # request
    if ret == {'success': 'OK'}:
        return redirect("/")
    elif ret == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Пользователь")
    else:
        message = "Что-то пошло не так при удалении пользователя"
        return render_template("error_templates/delete_error.html", message=message)


@app.route('/courses', methods=['GET', 'POST'])
def courses():  # просмотр курсов пользователя
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    user_courses = get(root + '/rest_courses/' + str(current_user.id)).json()["courses"]
    return render_template('course_templates/courses.html', courses=user_courses,
                           back_button_hidden='true', back_url='/dictionary')


@app.route('/make_course', methods=['GET', 'POST'])
def make_course():  # создание нового курса
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    form = CoursesForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)
        new_course = Courses()
        new_course.name = form.name.data
        new_course.about = form.about.data
        user.courses.append(new_course)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/courses')
    return render_template('course_templates/make_course.html', form=form, back_url="/courses")


@app.route('/course/<int:course_id>', methods=['GET', 'POST'])
def course_view(course_id):  # просмотр курса
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    course_response = get(root + '/rest_course/' + str(course_id)).json()
    if course_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Курс")
    course = course_response["course"]
    course_users_id = [user["id"] for user in course["users"]]
    if current_user.id not in course_users_id:
        return render_template("access_denied.html", back_button_hidden="true",
                               message="У вас нет доступа к этому курсу.")
    if course['about']:
        python_data = {"course_about": course['about'].split("\n")}
    else:
        python_data = {"course_about": []}
    if not current_user.teacher:
        return render_template('course_templates/course_view.html', course=course, back_url="/courses",
                               current_user=current_user,
                               python_data=python_data)
    form = CoursesForm()
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        course = db_sess.query(Courses).get(course_id)
        course.name = form.name.data
        course.about = form.about.data
        if course.about:
            python_data = {"course_about": course.about.split("\n")}
        else:
            python_data = {"course_about": []}
        user = db_sess.query(User).get(current_user.id)
        user.courses.append(course)
        db_sess.merge(user)
        db_sess.commit()
        return render_template('course_templates/course_view.html', course=course, back_url="/courses",
                               form=form,
                               current_user=current_user,
                               python_data=python_data)
    return render_template('course_templates/course_view.html', course=course, back_url="/courses", form=form,
                           current_user=current_user,
                           python_data=python_data)


@app.route('/course_statistics/<int:course_id>', methods=['GET', 'POST'])
def course_statistics(course_id):  # статистика курса
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    if not course:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Курс")
    if current_user not in course.users:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    if course.about:
        python_data = {"course_about": course.about.split("\n")}
    else:
        python_data = {"course_about": []}
    lessons_data = {}
    pupil_count = 0
    for lesson in course.lessons:
        pupil_count = 0
        lesson_percentage = 0
        completed_lesson = 0
        started_lesson = 0
        unstarted_lesson = 0
        for user in course.users:
            if not user.teacher:
                pupil_count += 1
                res = lesson_learned(lesson.id, user.id)
                lesson_percentage += res[0]
                if res[0] == 100:
                    completed_lesson += 1
                elif res[0] == 0:
                    unstarted_lesson += 1
                else:
                    started_lesson += 1
        if pupil_count:
            lesson_percentage = int(lesson_percentage / pupil_count)
        else:
            lesson_percentage = 0
        lessons_data[lesson.id] = (
            lesson_percentage, completed_lesson, started_lesson, unstarted_lesson)
    return render_template("course_templates/course_statistics.html", course=course, lessons_data=lessons_data,
                           len_course_lessons=len(course.lessons),
                           len_course_pupils=pupil_count, python_data=python_data,
                           back_url=f"/courses")


@app.route('/course/<int:course_id>/pupils', methods=['GET', 'POST'])
def course_pupils_view(course_id):  # добавление учеников к курсу
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    course_response = get(root + '/rest_course/' + str(course_id)).json()
    if course_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Курс")
    course = course_response["course"]
    if course_id not in [c.id for c in user.courses]:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    form = AddItemToSomethingForm()
    all_users = get(root + '/rest_users').json()["users"]
    all_items = list(filter(lambda x: x["creator"] == current_user.id and not x["teacher"],
                            all_users))
    max_id = max([item["id"] for item in all_items])
    course_users_ids = [u["id"] for u in course["users"]]
    added_items = list(filter(lambda x: x["id"] in course_users_ids, all_items))
    not_added_items = list(filter(lambda x: x not in course["users"], all_items))
    items_js = {
        "all_items": all_items,
        "added_items": added_items,
        "not_added_items": not_added_items,
        "max_id": max_id
    }
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        pupils_js = request.form.getlist('form-res')
        str_arr = pupils_js[0]
        course = db_sess.query(Courses).get(course_id)
        ans_arr = [int(item) for item in str_arr.split(",")]
        for pupil_js in all_items:
            pupil = db_sess.query(User).get(pupil_js["id"])
            if ans_arr[pupil_js["id"]]:
                pupil.courses.append(course)
                db_sess.merge(pupil)
            else:
                if pupil in course.users:
                    pupil.courses.remove(course)
                    db_sess.merge(pupil)
        db_sess.commit()
        return redirect("/course/" + str(course_id))
    return render_template('user_templates/course_pupils.html',
                           back_url="/course/" + str(course_id),
                           max_items_number_on_one_page=60,
                           form=form, items_js=items_js)


@app.route('/delete_course/<int:course_id>', methods=['GET', 'POST'])
def delete_course(course_id):  # удалить курс
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    if not course:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Курс")
    if current_user not in course.users:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    ret = delete(root + "/rest_course/" + str(course_id)).json()
    if ret == {'success': 'OK'}:
        return redirect("/courses")
    elif ret == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Курс")
    else:
        return render_template("error_templates/delete_error.html", message="Что-то пошло не так при удалении курса",
                               back_button_hidden="true")


@app.route('/course/<int:course_id>/lesson/<int:lesson_id>', methods=['GET', 'POST'])
def lesson_view(course_id, lesson_id):  # просмотр урока
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    if course_id not in [c.id for c in user.courses]:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    lesson_response = get(root + '/rest_lesson/' + str(lesson_id)).json()
    if lesson_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    lesson = lesson_response["lesson"]
    db_sess = db_session.create_session()
    all_items = lesson["words"]
    items_js = {"all_items": all_items}
    max_items_number_on_one_page = 13
    if not current_user.teacher:
        max_items_number_on_one_page = 26
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
            return render_template('lesson_templates/lesson_view.html', lesson_data=lesson, course_id=course_id,
                                   back_url=f"/course/{course_id}",
                                   test_results=test_results,
                                   trainer_results=trainer_results,
                                   len_test_results=len(test_results),
                                   words_learn_states=words_learn_states, form=form,
                                   lesson_name=lesson_name, items_js=items_js,
                                   max_items_number_on_one_page=max_items_number_on_one_page)
        return render_template('lesson_templates/lesson_view.html', lesson_data=lesson, course_id=course_id,
                               back_url=f"/course/{course_id}",
                               test_results=test_results,
                               trainer_results=trainer_results,
                               len_test_results=len(test_results),
                               words_learn_states=words_learn_states, form=form,
                               lesson_name=lesson_name, items_js=items_js,
                               max_items_number_on_one_page=max_items_number_on_one_page)

    return render_template('lesson_templates/lesson_view.html', lesson_data=lesson, course_id=course_id,
                           back_url=f"/course/{course_id}", test_results=test_results,
                           trainer_results=trainer_results,
                           len_test_results=len(test_results),
                           words_learn_states=words_learn_states, lesson_name=lesson.name,
                           items_js=items_js,
                           max_items_number_on_one_page=max_items_number_on_one_page)


@app.route('/make_lesson/<int:course_id>', methods=['GET', 'POST'])
def make_lesson(course_id):  # создать урок
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    current_course = db_sess.query(Courses).get(course_id)
    if not current_course:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Курс")
    user = db_sess.query(User).get(current_user.id)
    if course_id not in [c.id for c in user.courses]:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    form = LessonsForm()
    all_trainers = db_sess.query(Trainers).all()
    all_tests = db_sess.query(Tests).all()
    if form.validate_on_submit():
        new_lesson = Lessons()
        new_lesson.name = form.name.data
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
        return redirect('/course/' + str(course_id))
    return render_template('lesson_templates/make_lesson.html', form=form, back_url=f"/course/{course_id}",
                           trainers=all_trainers, tests=all_tests,
                           len_trainers=len(all_trainers), len_tests=len(all_tests))


@app.route('/add_trainers_to_lesson/<int:lesson_id>', methods=['GET', 'POST'])
def add_trainers_to_lesson(lesson_id):  # добавление тренажеров к уроку
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    if not lesson:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    current_course = lesson.courses[0]
    user = db_sess.query(User).get(current_user.id)
    if current_course.id not in [c.id for c in user.courses]:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    form = AddSomethingToLessonForm()
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
        return redirect('/course/' + str(current_course.id) + '/lesson/' + str(lesson_id))
    return render_template('lesson_templates/tasks_templates/add_trainers_to_lesson.html', trainers=all_trainers,
                           form=form,
                           len_trainers=len(all_trainers),
                           lesson_trainers=lesson_trainers, unused_trainers=unused_trainers)


@app.route('/add_tests_to_lesson/<int:lesson_id>', methods=['GET', 'POST'])
def add_tests_to_lesson(lesson_id):  # добавление тестов к уроку
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    if not lesson:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    current_course = lesson.courses[0]
    user = db_sess.query(User).get(current_user.id)
    if current_course.id not in [c.id for c in user.courses]:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    form = AddSomethingToLessonForm()
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
        return redirect('/course/' + str(current_course.id) + '/lesson/' + str(lesson_id))
    return render_template('lesson_templates/tasks_templates/add_tests_to_lesson.html', tests=all_tests, form=form,
                           len_tests=len(all_tests),
                           lesson_tests=lesson_tests, unused_tests=unused_tests)


@app.route('/add_words_to_lesson/<int:lesson_id>', methods=['GET', 'POST'])
def add_words_to_lesson(lesson_id):  # добавляет слова к уроку
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    lesson_response = get(root + "/rest_lesson/" + str(lesson_id)).json()
    if lesson_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    form = AddSomethingToLessonForm()
    lesson = lesson_response["lesson"]
    current_course_id = lesson["course"]["id"]
    all_items = get(root + "/rest_dict").json()["words"]
    max_id = max([item["id"] for item in all_items])
    my_items = list(filter(lambda x: x["author"] == current_user.id, all_items))
    rest_items = list(filter(lambda x: x["author"] != current_user.id, all_items))
    added_items = lesson["words"]
    not_added_items = list(filter(lambda x: x not in added_items, all_items))
    other_user_lessons = list(filter(lambda x: x["id"] != lesson_id, user_lessons))
    other_lesson_words = []
    for les in other_user_lessons:
        for word in les["words"]:
            if word not in other_lesson_words:
                other_lesson_words.append(word)
    course_items = other_lesson_words
    course_items_id = [item["id"] for item in course_items]
    not_course_items = list(filter(lambda x: x["id"] not in course_items_id, all_items))
    items_js = {
        "max_id": max_id,
        "all_items": all_items,
        "my_items": my_items,
        "rest_items": rest_items,
        "added_items": added_items,
        "not_added_items": not_added_items,
        "course_items": course_items,
        "not_course_items": not_course_items
    }
    db_sess = db_session.create_session()
    current_course = db_sess.query(Courses).get(current_course_id)
    lesson = db_sess.query(Lessons).get(lesson_id)
    if form.validate_on_submit():
        items_js = request.form.getlist('form-res')
        str_arr = items_js[0]
        ans_arr = [int(item) for item in str_arr.split(",")]
        removed_word = True
        for word_js in all_items:
            word = db_sess.query(Words).get(word_js["id"])
            if ans_arr[word_js["id"]]:
                lesson.words.append(word)
            else:
                if word in lesson.words:
                    lesson.words.remove(word)
                    removed_word = True
        if removed_word:
            test_results = db_sess.query(TestsToUsers).filter(
                TestsToUsers.course_id == current_course_id,
                TestsToUsers.lesson_id == lesson_id).all()
            for test_res in test_results:
                db_sess.delete(test_res)
        current_course.lessons.append(lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/course/' + str(current_course_id) + '/lesson/' + str(lesson_id))
    return render_template('lesson_templates/word_templates/add_words_to_lesson.html',
                           back_url='/course/' + str(current_course_id) + '/lesson/' + str(
                               lesson_id),
                           max_items_number_on_one_page=60,
                           form=form, items_js=items_js)


@app.route('/course/<int:course_id>/lesson_delete/<int:lesson_id>', methods=['GET', 'POST'])
def delete_lesson(course_id, lesson_id):  # удаление урока
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    lesson_response = get(root + "/rest_lesson/" + str(lesson_id)).json()
    if lesson_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    ret = delete(root + "/rest_lesson/" + str(lesson_id)).json()
    if ret == {'success': 'OK'}:
        return redirect("/course/" + str(course_id))
    else:
        return render_template("error_templates/delete_error.html", message="Что-то пошло не так при удалении урока",
                               back_button_hidden="true")


@app.route('/course/<int:course_id>/lesson_statistics/<int:lesson_id>', methods=['GET', 'POST'])
def lesson_statistics(course_id, lesson_id):  # статистика урока
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    lesson_response = get(root + "/rest_lesson/" + str(lesson_id)).json()
    if lesson_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
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
                WordsToUsers.words == int(w["id"])).first()
            if w_learn_state:
                w_learn_state = w_learn_state.learn_state
            else:
                w_learn_state = 0
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
    python_data = {"course_pupils": course_pupils}
    lesson_percentage = 0
    les = db_sess.query(Lessons).get(lesson_id)
    for user in db_sess.query(Courses).get(course_id).users:
        if not user.teacher:
            res = lesson_learned(les.id, user.id)[0]
            lesson_percentage += res
    return render_template("lesson_templates/lesson_statistics.html", lesson_name=lesson["name"],
                           back_url=f"/course/{course_id}",
                           lesson_words_len=len(lesson["words"]),
                           lesson_trainers_len=len(lesson["trainers"]),
                           lesson_tests_len=len(lesson["tests"]),
                           course_pupils=course_pupils, course_id=course_id, lesson_id=lesson_id,
                           lesson_percentage=lesson_percentage, python_data=python_data)


@app.route('/course/<int:course_id>/lesson_statistics/<int:lesson_id>/pupil/<int:pupil_id>',
           methods=['GET', 'POST'])
def lesson_pupil_statistics(course_id, lesson_id, pupil_id):  # статистика ученика по уроку
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    lesson_response = get(root + "/rest_lesson/" + str(lesson_id)).json()
    if lesson_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
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
    lesson_name = lesson["name"]
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
    return render_template("lesson_templates/lesson_pupil_statistics.html", pupil=pupil,
                           back_url=f"/course/{course_id}/lesson_statistics/{lesson_id}",
                           words_learned=words_learned,
                           words_viewed=words_viewed,
                           trainers_completed=trainers_completed,
                           trainers_uncompleted=trainers_uncompleted,
                           tests_completed=tests_completed,
                           tests_uncompleted=tests_uncompleted, lesson_name=lesson_name)


@app.route("/delete_word_from_lesson/<int:lesson_id>/<int:word_id>", methods=['GET'])
def delete_word_from_lesson(lesson_id, word_id):  # удаление слова от урока
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    if not lesson:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    word = db_sess.query(Words).get(word_id)
    if not word:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Слово", message="Слово не найдено")
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    if word in lesson.words:
        current_course = lesson.courses[0]
        lesson.words.remove(word)
        test_results = db_sess.query(TestsToUsers).filter(
            TestsToUsers.course_id == current_course.id,
            TestsToUsers.lesson_id == lesson_id,
            TestsToUsers.user_id == current_user.id).all()
        for test in test_results:
            db_sess.delete(test)
        db_sess.merge(lesson)
        db_sess.commit()
        return redirect('/course/' + str(current_course.id) + "/lesson/" + str(lesson_id))
    message = "Что-то пошло не так при удалении слова"
    return render_template("error_templates/delete_error.html", message=message)


@app.route("/delete_trainer_from_lesson/<int:lesson_id>/<int:trainer_id>", methods=['GET'])
def delete_trainer_from_lesson(lesson_id, trainer_id):  # удаление тренажера от урока
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    if not lesson:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    trainer = db_sess.query(Trainers).get(trainer_id)
    if not trainer:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Тренажер")
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    if trainer in lesson.trainers:
        lesson.trainers.remove(trainer)
        db_sess.merge(lesson)
        db_sess.commit()
        current_course = lesson.courses[0]
        return redirect('/course/' + str(current_course.id) + "/lesson/" + str(lesson_id))
    message = "Что-то пошло не так при удалении тренажера"
    return render_template("error_templates/delete_error.html", message=message)


@app.route("/delete_test_from_lesson/<int:lesson_id>/<int:test_id>", methods=['GET'])
def delete_test_from_lesson(lesson_id, test_id):  # удаление теста от урока
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    if not lesson:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Урок")
    test = db_sess.query(Tests).get(test_id)
    if not test:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Тест")
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    if test in lesson.tests:
        lesson.tests.remove(test)
        db_sess.merge(lesson)
        db_sess.commit()
        current_course = lesson.courses[0]
        return redirect('/course/' + str(current_course.id) + "/lesson/" + str(lesson_id))
    message = "Что-то пошло не так при удалении теста"
    return render_template("error_templates/delete_error.html", message=message)


@app.route('/dictionary', methods=['GET', 'POST'])
def dict_view():  # просмотр словаря
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
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
    db_sess = db_session.create_session()
    # print([w.id for w in db_sess.query(Words).all()])
    # print(items_js)  # ff
    # print([w['id'] for w in all_words])
    max_words_number_on_one_page = 32
    return render_template("lesson_templates/word_templates/dictionary.html", all_words=all_words,
                           current_user=current_user,
                           len_all_words=len_all_words,
                           my_words=my_words, rest_words=rest_words,
                           back_button_hidden="true", items_js=items_js,
                           max_items_number_on_one_page=max_words_number_on_one_page)


@app.route('/add_word', methods=['GET', 'POST'])
def add_word():  # добавление слова в словарь
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    form = WordsForm()
    db_sess = db_session.create_session()
    image_start_preview = "/static/words_data/tutorial_down.png"
    all_words = get(root + "/rest_dict").json()["words"]
    python_data = {"json_all_words": all_words}
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
        fex1 = "." + transcription_audio.filename.split(".")[-1]
        fex2 = "." + phrase_audio.filename.split(".")[-1]
        fex3 = "." + translation_audio.filename.split(".")[-1]
        path_to_file = os.path.dirname(__file__)
        full_path = os.path.join(path_to_file)
        save_name = str(hash(str(new_word.id) + "_" + str(new_word.author) + "_" +
                             str(new_word.translation) + "_" + str(new_word.hieroglyph)))
        filepath = os.path.join(full_path, "static", "words_data", save_name)
        if image:
            image.save(filepath + "_image.png")
            new_word.image = save_name + "_image.png"
        else:
            new_word.image = "undefined_image.png"

        if transcription_audio:
            audfname = filepath + "_trans_audio" + fex1
            transcription_audio.save(audfname)
            x = AudioSegment.from_file(audfname)
            os.remove(audfname)
            x.export(audfname.replace(fex1, ".wav"), format='wav')
            new_word.front_side_audio = save_name + "_trans_audio.wav"
            new_word.right_side_audio = save_name + "_trans_audio.wav"
        else:
            new_word.front_side_audio = "undefined_trans_audio.wav"
            new_word.right_side_audio = "undefined_trans_audio.wav"
        if phrase_audio:
            audfname = filepath + "_phrase_audio" + fex2
            phrase_audio.save(audfname)
            x = AudioSegment.from_file(audfname)
            os.remove(audfname)
            x.export(audfname.replace(fex2, ".wav"), format='wav')
            new_word.up_side_audio = save_name + "_phrase_audio.wav"
            new_word.left_side_audio = save_name + "_phrase_audio.wav"
        else:
            new_word.up_side_audio = "undefined_phrase_audio.wav"
            new_word.left_side_audio = "undefined_phrase_audio.wav"
        if translation_audio:
            audfname = filepath + "_translation_audio" + fex3
            translation_audio.save(audfname)
            x = AudioSegment.from_file(audfname)
            os.remove(audfname)
            x.export(audfname.replace(fex3, ".wav"), format='wav')
            new_word.down_side_audio = save_name + "_translation_audio.wav"
        else:
            new_word.down_side_audio = "undefined_translation_audio.wav"

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
    return render_template('lesson_templates/word_templates/make_word.html', form=form, filename="tmp",
                           image_start_preview=image_start_preview,
                           back_url="/dictionary",
                           all_words=all_words, python_data=python_data)


@app.route('/delete_word/<int:word_id>', methods=['GET', 'POST'])
def delete_word(word_id):  # удаление слова
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not current_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    if word_id not in [w.id for w in current_user.words]:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    ret = delete(root + "/rest_word/" + str(word_id)).json()
    if ret == {'success': 'OK'}:
        return redirect("/dictionary")
    elif ret == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Слово", message="Слово не найдено")
    message = "Что-то пошло не так при удалении слова"
    return render_template("error_templates/delete_error.html", message=message + "\n" + str(ret))  # ff


@app.route('/dict_word/<int:word_id>', methods=['GET', 'POST'])
def dict_word_view(word_id):  # просмотр слова
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    word_response = get(root + '/rest_word/' + str(word_id)).json()
    if word_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Слово", message="Слово не найдено")
    word = word_response["word"]
    all_words = get(root + "/rest_dict").json()["words"]
    prev_id = word_id
    next_id = word_id
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
    python_data = {
        "word_data": {
            "hieroglyph": word["hieroglyph"],
            "translation": word["translation"],
            "transcription": word["transcription"],
            "phrase_ch": word["phrase_ch"],
            "phrase_ru": word["phrase_ru"]
        },
        "audio_urls": {
            "front_audio": url_for("static", filename="/words_data/" + word["front_side_audio"]),
            "left_audio": url_for("static", filename="/words_data/" + word["left_side_audio"]),
            "right_audio": url_for("static", filename="/words_data/" + word["right_side_audio"]),
            "up_audio": url_for("static", filename="/words_data/" + word["up_side_audio"]),
            "down_audio": url_for("static", filename="/words_data/" + word["down_side_audio"])
        }
    }

    return render_template('lesson_templates/word_templates/word_view.html', header_disabled="true",
                           python_data=python_data,
                           image_name=url_for("static", filename="words_data/" + word["image"]),
                           back_url="/dictionary",
                           dict=all_words,
                           prev_button_visibility=prev_button_visibility,
                           next_button_visibility=next_button_visibility,
                           prev_word_url="/dict_word/" + str(prev_id),
                           next_word_url="/dict_word/" + str(next_id),
                           words_learn_state=0,
                           hints_enabled=int(current_user.hints_enabled))


@app.route('/course/<int:course_id>/lesson_word/<int:lesson_id>/word/<int:word_id>',
           methods=['GET', 'POST'])
def lesson_word_view(course_id, lesson_id, word_id):  # просмотр слова в уроке
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    word_response = get(root + '/rest_word/' + str(word_id)).json()
    if word_response == {'message': 'Object not found'}:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Слово", message="Слово не найдено")
    word = word_response["word"]
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    lesson = get(root + '/rest_lesson/' + str(lesson_id)).json()["lesson"]
    lesson_words = lesson["words"]
    ret = post(
        root + f"/rest_word_view_recording/{current_user.id}/{word_id}")  # запись того, что пользователь просмотрел слово
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
        trainer_href = f"/course/{course_id}/lesson/{lesson_id}/trainer/{first_trainer_id}"
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
    python_data = {
        "word_data": {
            "hieroglyph": word["hieroglyph"],
            "translation": word["translation"],
            "transcription": word["transcription"],
            "phrase_ch": word["phrase_ch"],
            "phrase_ru": word["phrase_ru"]
        },
        "audio_urls": {
            "front_audio": url_for("static", filename="/words_data/" + word["front_side_audio"]),
            "left_audio": url_for("static", filename="/words_data/" + word["left_side_audio"]),
            "right_audio": url_for("static", filename="/words_data/" + word["right_side_audio"]),
            "up_audio": url_for("static", filename="/words_data/" + word["up_side_audio"]),
            "down_audio": url_for("static", filename="/words_data/" + word["down_side_audio"])
        }
    }
    return render_template('lesson_templates/word_templates/word_view.html', header_disabled="true",
                           python_data=python_data,
                           image_name=url_for("static", filename="words_data/" + word["image"]),
                           back_url="/course/" + str(course_id) + "/lesson/" + str(lesson_id),
                           dict=lesson_words,
                           prev_button_visibility=prev_button_visibility,
                           next_button_visibility=next_button_visibility,
                           prev_word_url=f"/course/{str(course_id)}/lesson_word/{str(lesson_id)}/word/{str(prev_id)}",
                           next_word_url=f"/course/{str(course_id)}/lesson_word/{str(lesson_id)}/word/{str(next_id)}",
                           words_learn_state=words_learn_state, trainer_href=trainer_href,
                           hints_enabled=int(current_user.hints_enabled))


@app.route('/course/<int:course_id>/lesson/<int:lesson_id>/trainer/<int:trainer_id>',
           methods=['GET', 'POST'])
def lesson_trainer_view(course_id, lesson_id, trainer_id):  # просмотр тренажера
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    trainer = db_sess.query(Trainers).get(trainer_id)
    lesson = get(root + '/rest_lesson/' + str(lesson_id)).json()["lesson"]
    lesson_trainers = lesson["trainers"]
    lesson_tests = lesson["tests"]
    lesson_words = db_sess.query(Lessons).get(lesson_id).words
    all_words = db_sess.query(Words).all()
    python_data = {
        "all_words": t_word_to_javascript(all_words),
        "lesson_words": t_word_to_javascript(lesson_words)
    }

    is_last_trainer = False
    next_trainer_href = ""
    next_test_href = ""
    if lesson_trainers[-1]["id"] == trainer_id:
        is_last_trainer = True
        if len(lesson_tests) != 0:
            next_test_href = \
                f"/course/{course_id}/lesson/{lesson_id}/test/{lesson_tests[0]['id']}"
    else:
        for i in range(len(lesson_trainers)):
            t = lesson_trainers[i]
            if t["id"] == trainer_id:
                next_trainer_href = \
                    f"/course/{course_id}/lesson/{lesson_id}/trainer/{lesson_trainers[i + 1]['id']}"
                break
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
    answer_button_number_first_line = 3
    answer_button_number_second_line = 3
    answer_button_number = answer_button_number_first_line + answer_button_number_second_line
    return render_template('lesson_templates/tasks_templates/trainer_view.html', course=course, lesson=lesson,
                           trainer=trainer,
                           answer_button_number_first_line=answer_button_number_first_line,
                           answer_button_number_second_line=answer_button_number_second_line,
                           answer_button_number=answer_button_number,
                           back_url=f"/course/{course_id}/lesson/{lesson_id}",
                           is_last_trainer=is_last_trainer, next_trainer_href=next_trainer_href,
                           next_test_href=next_test_href, python_data=python_data)


@app.route('/course/<int:course_id>/lesson/<int:lesson_id>/trainer/<int:trainer_id>/result',
           methods=['GET', 'POST'])
def trainer_result(course_id, lesson_id, trainer_id):  # запись результата прохождения тренажера
    if request.method != 'POST':
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
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


@app.route('/course/<int:course_id>/lesson/<int:lesson_id>/test/<int:test_id>',
           methods=['GET', 'POST'])
def lesson_test_view(course_id, lesson_id, test_id):  # просмотр тестов урока
    if not current_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    lessons_response = get(root + '/rest_user_lessons/' + str(current_user.id)).json()
    user_lessons = lessons_response["user_lessons"]
    lessons = [item["id"] for item in user_lessons]
    if lesson_id not in lessons:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    lesson = db_sess.query(Lessons).get(lesson_id)
    test = db_sess.query(Tests).get(test_id)
    all_tests = db_sess.query(Tests).all()

    les = get(root + '/rest_lesson/' + str(lesson_id)).json()
    lesson_tests = les["lesson"]["tests"]
    lesson_words = db_sess.query(Lessons).get(lesson_id).words
    all_words = db_sess.query(Words).all()
    python_data = {
        "all_words": t_word_to_javascript(all_words),
        "lesson_words": t_word_to_javascript(lesson_words)
    }
    answer_button_number_first_line = 3
    answer_button_number_second_line = 3
    answer_button_number = answer_button_number_first_line + answer_button_number_second_line

    is_last_test = False
    next_test_href = ""
    if lesson_tests[-1]["id"] == test_id:
        is_last_test = True
    else:
        for i in range(len(lesson_tests)):
            t = lesson_tests[i]
            if t["id"] == test_id:
                next_test_href = \
                    f"/course/{course_id}/lesson/{lesson_id}/test/{lesson_tests[i + 1]['id']}"
                break

    tests_list = []
    for i in range(len(lesson.words)):
        rand_num = random.randint(0, len(all_tests) - 2)
        rand_test = all_tests[rand_num]
        tests_list.append(str(rand_test.check_side) + " " + str(rand_test.ans_side))
    tests_list = "  ".join(tests_list)
    if test.check_side == -1 and test.ans_side == -1:
        return render_template('lesson_templates/tasks_templates/ultimate_test_view.html', course=course, lesson=lesson,
                               test=test,
                               python_data=python_data,
                               back_url=f"/course/{course_id}/lesson/{lesson_id}",
                               tests_list=tests_list, is_last_test=is_last_test,
                               next_test_href=next_test_href,
                               answer_button_number_first_line=answer_button_number_first_line,
                               answer_button_number_second_line=answer_button_number_second_line,
                               answer_button_number=answer_button_number)
    return render_template('lesson_templates/tasks_templates/test_view.html', course=course, lesson=lesson, test=test,
                           python_data=python_data,
                           back_url=f"/course/{course_id}/lesson/{lesson_id}",
                           is_last_test=is_last_test, next_test_href=next_test_href,
                           answer_button_number_first_line=answer_button_number_first_line,
                           answer_button_number_second_line=answer_button_number_second_line,
                           answer_button_number=answer_button_number)


@app.route('/course/<int:course_id>/lesson/<int:lesson_id>/test/<int:test_id>/result',
           methods=['GET', 'POST'])
def test_result(course_id, lesson_id, test_id):
    if request.method != 'POST':  # запись результата прохождения теста
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
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
def change_word(word_id):  # изменить слово
    db_sess = db_session.create_session()
    cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
    if not cur_user.is_authenticated:
        return render_template("error_templates/unauthorized.html", back_button_hidden="true",
                               header_disabled="true")
    if not cur_user.teacher:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")

    new_word = db_sess.query(Words).get(word_id)
    if not new_word:
        return render_template("error_templates/object_not_found.html", back_button_hidden="true",
                               header_disabled="true", object="Слово", message="Слово не найдено")
    if word_id not in [w.id for w in cur_user.words]:
        return render_template("error_templates/access_denied.html", back_button_hidden="true")
    form = WordsForm()
    all_words = db_sess.query(Words).all()
    ret_all_words = list(filter(lambda item: int(item["id"]) != word_id,
                                get(root + "/rest_dict").json()["words"]))

    python_data = {"json_all_words": ret_all_words}

    path_to_file = os.path.dirname(__file__)
    full_path = os.path.join(path_to_file)

    prev_hieroglyph = new_word.hieroglyph
    prev_translation = new_word.translation
    prev_transcription = new_word.transcription
    prev_phrase_ch = new_word.phrase_ch
    prev_phrase_ru = new_word.phrase_ru

    image_file = Image.open(os.path.join(full_path, "static", "words_data", new_word.image))

    fn1 = os.path.join(full_path, "static", "words_data", new_word.front_side_audio)
    fn2 = os.path.join(full_path, "static", "words_data", new_word.up_side_audio)
    fn3 = os.path.join(full_path, "static", "words_data", new_word.down_side_audio)
    undefined_path = os.path.join(full_path, "static", "words_data", "undefined")
    if os.path.exists(fn1):
        transcription_audio_file = wave.open(fn1, mode="rb")
    else:
        transcription_audio_file = wave.open(undefined_path + "_trans_audio.wav", mode="rb")
        new_word.front_side_audio = "undefined_trans_audio.wav"
        new_word.right_side_audio = "undefined_trans_audio.wav"
    if os.path.exists(fn2):
        phrase_audio_file = wave.open(fn2, mode="rb")
    else:
        phrase_audio_file = wave.open(undefined_path + "_phrase_audio.wav", mode="rb")
        new_word.up_side_audio = "undefined_phrase_audio.wav"
        new_word.left_side_audio = "undefined_phrase_audio.wav"
    if os.path.exists(fn3):
        translation_audio_file = wave.open(fn3, mode="rb")
    else:
        translation_audio_file = wave.open(undefined_path + "_translation_audio.wav", mode="rb")
        new_word.down_side_audio = "undefined_translation_audio.wav"
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
        new_word.author = cur_user.id
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
        save_name = str(hash(str(new_word.id) + "_" + str(new_word.author) + "_" +
                             str(new_word.translation) + "_" + str(new_word.hieroglyph)))
        filepath = os.path.join(full_path, "static", "words_data", save_name)
        if image:
            image.save(filepath + "_image.png")
            new_word.image = save_name + "_image.png"
        if transcription_audio:
            transcription_audio.save(filepath + "_trans_audio.wav")
            new_word.front_side_audio = save_name + "_trans_audio.wav"
            new_word.right_side_audio = save_name + "_trans_audio.wav"
        else:
            new_word.front_side_audio = "undefined_trans_audio.wav"
            new_word.right_side_audio = "undefined_trans_audio.wav"
        if phrase_audio:
            phrase_audio.save(filepath + "_phrase_audio.wav")
            new_word.up_side_audio = save_name + "_phrase_audio.wav"
            new_word.left_side_audio = save_name + "_phrase_audio.wav"
        else:
            new_word.up_side_audio = "undefined_phrase_audio.wav"
            new_word.left_side_audio = "undefined_phrase_audio.wav"
        if translation_audio:
            translation_audio.save(filepath + "_translation_audio.wav")
            new_word.down_side_audio = save_name + "_translation_audio.wav"
        else:
            new_word.down_side_audio = "undefined_translation_audio.wav"
        new_word.creation_time = dt.datetime.now()
        cur_user = db_sess.query(User).filter(User.id == cur_user.id).first()
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
    return render_template('lesson_templates/word_templates/make_word.html', form=form, dictionary=all_words,
                           filename="tmp",
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
                           all_words=all_words, python_data=python_data)


def main():
    db_session.global_init("db/users.db")
    app.run(host='0.0.0.0')


if __name__ == '__main__':
    main()
