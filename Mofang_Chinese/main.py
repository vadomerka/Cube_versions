from flask import Flask, render_template, redirect, url_for
from flask import request, make_response, session, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api

# tables
from data import db_session
from data.words import Words, words_to_lesson, WordsToUsers
from data.lessons import Lessons, lessons_to_course
from data.courses import Courses, users_to_course
from data.users import User
from data.trainers import Trainers
from data.tests import Tests, TestsToUsers

# forms
from forms.user import MakeUserForm, MakePasswordForm, LoginForm
from forms.course import CoursesForm, AddUsersToCourseForm
from forms.lesson import LessonsForm, AddWordsToLessonForm, AddTrainersToLessonForm, \
    AddTestsToLessonForm
from forms.word import WordsForm

# resourses
from resourses.course_resourses import CourseListResource, CourseResource
from resourses.dict_resourses import DictResourse, WordResourse
from resourses.lesson_resourses import LessonResource
from resourses.user_resourses import UserResource, UserListResource
from requests import get, post, delete, put
import requests
from sqlalchemy import insert, create_engine
import os
import datetime as dt
from PIL import Image
import vlc

engine = create_engine('sqlite:///db/users.db', echo=True, future=True)
app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api.add_resource(CourseListResource, '/rest_courses/<int:user_id>')
api.add_resource(CourseResource, '/rest_course/<int:course_id>')
api.add_resource(DictResourse, "/rest_dict")
api.add_resource(WordResourse, "/rest_word/<int:word_id>")
api.add_resource(LessonResource, "/rest_lessons/<int:lesson_id>")
api.add_resource(UserResource, "/rest_user/<int:user_id>")
api.add_resource(UserListResource, "/rest_users")
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
    form = MakePasswordForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('change_password.html',
                                   form=form,
                                   user=user,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        user.set_password(form.password.data)
        db_sess.merge(user)
        db_sess.commit()
        return redirect('/')
    return render_template("change_password.html", user=user, form=form)


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
    return render_template("generate_link.html", user=user)


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
        return redirect("/pupils")
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


@app.route('/add_users_to_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def add_users_to_course(course_id):
    form = AddUsersToCourseForm()
    db_sess = db_session.create_session()
    users = get(root + "/rest_users").json()['users']
    course = db_sess.query(Courses).get(course_id)
    all_pupils = []
    course_pupils = []
    for user in users:
        if not user['teacher']:
            pupil = db_sess.query(User).get(user['id'])
            if pupil in course.users:
                course_pupils.append(pupil)
            all_pupils.append(pupil)
    if form.validate_on_submit():
        all_pupils = request.form.getlist('lesson_pupil')
        for pupils_id in list(all_pupils):
            pupil = db_sess.query(User).get(int(pupils_id))
            pupil.courses.append(course)

            db_sess.merge(pupil)
        not_lesson_pupils = request.form.getlist('not_lesson_pupil')
        for pupils_id in list(not_lesson_pupils):
            pupil = db_sess.query(User).get(int(pupils_id))
            if course in pupil.courses:
                pupil.courses.remove(course)

            db_sess.merge(pupil)
        db_sess.commit()

        return redirect('/courses/' + str(course_id))

    return render_template('add_users_to_course.html', form=form, pupils=all_pupils,
                           course_pupils=course_pupils,
                           back_button_hidden='false', back_url="/courses",
                           len_pupils=len(all_pupils))


# /home/rad/PycharmProjects/venv/lib/python3.6/site-packages/pip/_internal/cli/cmdoptions.py
# стандартная библеотека логов питона


@app.route('/courses_delete/<int:course_id>', methods=['GET', 'POST'])
@login_required
def delete_course(course_id):
    ret = delete(root + "/rest_course/" + str(course_id)).json()
    if ret == {'success': 'OK'}:
        return redirect("/courses")
    else:
        print("Couldn't delete course " + str(course_id))
        return redirect("/courses")


@app.route('/courses/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course_view(course_id):
    course = get(root + '/rest_course/' + str(course_id)
                 ).json()["course"]

    course_about = '&lt;br&lt;'.join(course["about"].split("\r\n"))
    course_about = '<<<<'.join(course["about"].split("\r\n"))

    return render_template('course_view.html', course_data=course, course_about=course_about,
                           back_button_hidden='false', back_url="/courses")


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
    return render_template('course_pupils.html', course=course, course_pupils=all_pupils,
                           back_button_hidden='false', back_url="/courses/" + str(course_id),
                           pupils_in_column_number=13, column_number=4, all_pupils_js=all_pupils_js,
                           my_pupils_js=my_pupils_js, rest_pupils_js=rest_pupils_js,
                           course_pupils_js=course_pupils_js,
                           not_course_pupils_js=not_course_pupils_js,
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
    lesson = get(root + '/rest_lessons/' + str(lesson_id)
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
    form = AddTrainersToLessonForm()
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
    form = AddTestsToLessonForm()
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
    form = AddWordsToLessonForm()
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
                           not_course_items_js=not_course_words_js, )


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
    ret = delete(root + "/rest_lessons/" + str(lesson_id)).json()
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
    image_start_preview = "/static/tutorial_down.png"
    # left_start_preview = "/static/tutorial_left.png"
    # right_start_preview = "/static/tutorial_right.png"
    # up_start_preview = "/static/tutorial_up.png"
    # down_start_preview = "/static/tutorial_down.png"
    if form.validate_on_submit():
        new_word = Words()
        new_word.author = current_user.id
        new_word.hieroglyph = form.hieroglyph.data
        new_word.translation = form.translation.data
        new_word.transcription = form.transcription.data
        new_word.phrase_ch = form.phrase_ch.data
        new_word.phrase_ru = form.phrase_ru.data
        # print(1, new_word.author)
        # print(2, new_word.hieroglyph)
        # print(3, new_word.translation)
        # print(4, new_word.transcription)
        # print(5, new_word.phrase_ch)
        # print(6, new_word.phrase_ru)
        # print(request.files)
        image = request.files['image']
        # left = request.files['left']
        # right = request.files['right']
        # up = request.files['up']
        # down = request.files['down']
        transcription_audio = request.files['transcription_audio']
        phrase_audio = request.files['phrase_audio']
        translation_audio = request.files['translation_audio']
        path_to_file = os.path.dirname(__file__)
        full_path = os.path.join(path_to_file)
        save_name = str(hash(
            str(new_word.author) + "_" + str(new_word.translation) + "_" + str(new_word.hieroglyph)))
        filepath = os.path.join(full_path, "static", save_name)
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
        new_word.time = dt.datetime.now()
        print(new_word.time)
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


@app.route('/add_words/<int:number>', methods=['GET', 'POST'])
@login_required
def add_words(number):
    if current_user.teacher == 1:
        data = {"author": current_user.id,
                "hieroglyph": "null",
                "translation": "null",
                "front_side": "undefined_image.png",
                "left_side": "undefined_image.png",
                "right_side": "undefined_image.png",
                "up_side": "undefined_image_up.png",
                "down_side": "undefined_image_down.png",
                "front_side_audio": "undefined_trans_audio.mp3",
                "left_side_audio": "undefined_translation_audio.mp3",
                "right_side_audio": "undefined_trans_audio.mp3",
                "up_side_audio": "undefined_phrase_audio.mp3",
                "down_side_audio": "undefined_trans_audio.mp3"}
        for i in range(number):
            ret = post(root + "/rest_dict", json=data, params=data)

        return redirect("/dictionary")
    return redirect("/dictionary")


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
    return render_template('word_view.html',
                           hieroglyph=word["hieroglyph"],
                           translation=word["translation"],
                           transcription=word["transcription"],
                           phrase_ch=word["phrase_ch"],
                           phrase_ru=word["phrase_ru"],
                           image_name=url_for("static", filename=word["image"]),
                           front_audio=url_for("static", filename=word["front_side_audio"]),
                           left_audio=url_for("static", filename=word["left_side_audio"]),
                           right_audio=url_for("static", filename=word["right_side_audio"]),
                           up_audio=url_for("static", filename=word["up_side_audio"]),
                           down_audio=url_for("static", filename=word["down_side_audio"]),
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
    word = get(root + '/rest_word/' + str(word_id)).json()["word"]
    lesson_words = get(root + '/rest_lessons/' + str(lesson_id)
                       ).json()["lesson"]["words"]

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
                           image_name=url_for("static", filename=word["image"]),
                           front_audio=url_for("static", filename=word["front_side_audio"]),
                           left_audio=url_for("static", filename=word["left_side_audio"]),
                           right_audio=url_for("static", filename=word["right_side_audio"]),
                           up_audio=url_for("static", filename=word["up_side_audio"]),
                           down_audio=url_for("static", filename=word["down_side_audio"]),
                           back_url="/courses/" + str(course_id) + "/lesson/" + str(lesson_id),
                           dict=lesson_words,
                           prev_button_visibility=prev_button_visibility,
                           next_button_visibility=next_button_visibility,
                           prev_word_url="/" + "courses/" + str(
                               course_id) + "/lesson_word/" + str(lesson_id) + "/word/" + str(
                               prev_id),
                           next_word_url="/" + "courses/" + str(
                               course_id) + "/lesson_word/" + str(lesson_id) + "/word/" + str(
                               next_id))


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
    all_words = db_sess.query(Words).all()

    lesson_words = db_list_to_javascript(lesson.words)
    lesson_all_words = db_list_to_javascript(all_words)

    answer_button_number = 6
    return render_template('test_view.html', course=course, lesson=lesson, test=test,
                           lesson_words=lesson_words, answer_button_number=answer_button_number,
                           back_url=f"/courses/{course_id}/lesson/{lesson_id}",
                           back_button_hidden="false", all_words=lesson_all_words)


@app.route('/courses/<int:course_id>/lesson/<int:lesson_id>/test/<int:test_id>/result',
           methods=['GET', 'POST'])
@login_required
def test_result(course_id, lesson_id, test_id):
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    lesson = db_sess.query(Lessons).get(lesson_id)

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

    front_file = Image.open(os.path.join(full_path, "static", new_word.front_side))
    left_file = Image.open(os.path.join(full_path, "static", new_word.left_side))
    right_file = Image.open(os.path.join(full_path, "static", new_word.right_side))
    up_file = Image.open(os.path.join(full_path, "static", new_word.up_side))
    down_file = Image.open(os.path.join(full_path, "static", new_word.down_side))

    transcription_audio_file = vlc.MediaPlayer(os.path.join(
        full_path, "static", new_word.front_side_audio))
    phrase_audio_file = vlc.MediaPlayer(os.path.join(full_path, "static", new_word.up_side_audio))
    translation_audio_file = vlc.MediaPlayer(
        os.path.join(full_path, "static", new_word.left_side_audio))

    if "undefined" not in new_word.front_side_audio:
        is_transcription_audio = "true"
    else:
        is_transcription_audio = "false"
    if "undefined" not in new_word.up_side_audio:
        is_phrase_audio = "true"
    else:
        is_phrase_audio = "false"
    if "undefined" not in new_word.left_side_audio:
        is_translation_audio = "true"
    else:
        is_translation_audio = "false"

    front_start_preview = "/static/" + new_word.front_side
    left_start_preview = "/static/" + new_word.left_side
    right_start_preview = "/static/" + new_word.right_side
    up_start_preview = "/static/" + new_word.up_side
    down_start_preview = "/static/" + new_word.down_side
    if form.validate_on_submit():
        new_word.author = current_user.id
        new_word.hieroglyph = form.hieroglyph.data
        new_word.translation = form.translation.data
        front = request.files['front']
        left = request.files['left']
        right = request.files['right']
        up = request.files['up']
        down = request.files['down']
        transcription_audio = request.files['transcription_audio']
        phrase_audio = request.files['phrase_audio']
        translation_audio = request.files['translation_audio']
        path_to_file = os.path.dirname(__file__)
        full_path = os.path.join(path_to_file)
        save_name = str(hash(
            str(new_word.author) + "_" + str(new_word.translation) + "_" + str(new_word.hieroglyph)))
        filepath = os.path.join(full_path, "static", save_name)
        if front:
            front.save(filepath + "_front.png")
            new_word.front_side = save_name + "_front.png"
        if left:
            left.save(filepath + "_left.png")
            new_word.left_side = save_name + "_left.png"
        if right:
            right.save(filepath + "_right.png")
            new_word.right_side = save_name + "_right.png"
        if up:
            up.save(filepath + "_up.png")
            new_word.up_side = save_name + "_up.png"
            im = Image.open(filepath + "_up.png")
            im.save(filepath + "_up_0.png")
            im = Image.open(filepath + "_up_0.png")
            im = im.transpose(Image.ROTATE_90)
            im.save(filepath + "_up_90.png")
            im = im.transpose(Image.ROTATE_90)
            im.save(filepath + "_up_180.png")
            im = im.transpose(Image.ROTATE_90)
            im.save(filepath + "_up_270.png")
        if down:
            down.save(filepath + "_down.png")
            new_word.down_side = save_name + "_down.png"
            im = Image.open(filepath + "_down.png")
            im.save(filepath + "_down_0.png")
            im = Image.open(filepath + "_down_0.png")
            im = im.transpose(Image.ROTATE_270)
            im.save(filepath + "_down_90.png")
            im = im.transpose(Image.ROTATE_270)
            im.save(filepath + "_down_180.png")
            im = im.transpose(Image.ROTATE_270)
            im.save(filepath + "_down_270.png")
        if transcription_audio:
            transcription_audio.save(filepath + "_trans_audio.mp3")
            new_word.front_side_audio = save_name + "_trans_audio.mp3"
            new_word.right_side_audio = save_name + "_trans_audio.mp3"
            new_word.down_side_audio = save_name + "_trans_audio.mp3"

        if phrase_audio:
            phrase_audio.save(filepath + "_phrase_audio.mp3")
            new_word.up_side_audio = save_name + "_phrase_audio.mp3"
        if translation_audio:
            translation_audio.save(filepath + "_translation_audio.mp3")
            new_word.left_side_audio = save_name + "_translation_audio.mp3"
        new_word.time = (dt.datetime.now() - datetime.datetime(2020, 1, 1)).total_seconds()
        cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
        cur_user.words.append(new_word)
        db_sess.commit()
        db_sess.close()
        return redirect('/dictionary')
    return render_template('make_word.html', form=form, dictionary=all_words, filename="tmp",
                           prev_hieroglyph=prev_hieroglyph, prev_translation=prev_translation,
                           front_file=front_file, left_file=left_file, right_file=right_file,
                           up_file=up_file, down_file=down_file,
                           transcription_audio_file=transcription_audio_file,
                           is_transcription_audio=is_transcription_audio,
                           phrase_audio_file=phrase_audio_file, is_phrase_audio=is_phrase_audio,
                           translation_audio_file=translation_audio_file,
                           is_translation_audio=is_translation_audio,
                           front_start_preview=front_start_preview,
                           left_start_preview=left_start_preview,
                           right_start_preview=right_start_preview,
                           up_start_preview=up_start_preview,
                           down_start_preview=down_start_preview)


def main():
    db_session.global_init("db/users.db")
    app.run()


if __name__ == '__main__':
    main()
