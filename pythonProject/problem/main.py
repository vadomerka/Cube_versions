# flask
from flask import Flask, render_template, redirect, url_for
from flask import request, make_response, session, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api

# tables
from data import db_session
from data.words import Words, words_to_lesson
from data.lessons import Lessons, lessons_to_course
from data.courses import Courses, users_to_course
from data.users import User
from data.trainers import Trainers

# forms
from forms.user import MakeUserForm, LoginForm
from forms.course import CoursesForm, AddUsersToCourseForm
from forms.lesson import LessonsForm, AddWordsToLessonForm, AddTrainersToLessonForm
from forms.word import WordsForm

# resourses
from resourses.course_resourses import CourseListResource, CourseResource
from resourses.dict_resourses import DictResourse, WordResourse
from resourses.lesson_resourses import LessonResource
from resourses.user_resourses import UserResource, UserListResource
from requests import get, post, delete, put
import requests

import os
import datetime as dt
from PIL import Image
import vlc

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api.add_resource(CourseListResource, '/rest_courses/<int:user_id>')
api.add_resource(CourseResource, '/rest_course/<int:course_id>')
api.add_resource(DictResourse, "/rest_dict")
api.add_resource(WordResourse, "/rest_word/<int:word_id>")
api.add_resource(LessonResource, "/rest_lessons/<int:lesson_id>")
api.add_resource(UserResource, "/rest_user/<int:id>")
api.add_resource(UserListResource, "/rest_users")
login_manager = LoginManager()
login_manager.init_app(app)


@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.courses:
            return redirect("/courses")
        return redirect("/dictionary")
    else:
        return redirect('/login')


# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     form = RegisterForm()
#     # print(form.validate_on_submit())
#     if form.validate_on_submit():
#         if form.password.data != form.password_again.data:
#             return render_template('register.html', title='Регистрация',
#                                    form=form,
#                                    message="Пароли не совпадают")
#         db_sess = db_session.create_session()
#         if db_sess.query(User).filter(User.email == form.email.data).first():
#             return render_template('register.html', title='Регистрация',
#                                    form=form,
#                                    message="Такой пользователь уже есть")
#         user = User(
#             name=form.name.data,
#             email=form.email.data,
#             about=form.about.data,
#             teacher=form.teacher.data
#         )
#         user.set_password(form.password.data)
#         db_sess.add(user)
#         db_sess.commit()
#         user = db_sess.query(User).filter(User.email == form.email.data).first()
#         if user and user.check_password(form.password.data):
#             login_user(user)
#             return redirect("/")
#         return render_template('register.html',
#                                message="Что-то пошло не так",
#                                form=form)
#     return render_template('register.html', title='Регистрация', form=form)


# response = requests.get('https://pythonexamples.org/', params=params)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(meta={'locales': ['ru']})
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


@app.route('/pupils', methods=['GET', 'POST'])
@login_required
def pupils():
    db_sess = db_session.create_session()
    users_pupils = []
    all_users = db_sess.query(User).all()
    for user in all_users:
        if user.creator == current_user.id:
            users_pupils.append(user)
    # print(users_pupils)
    # users_pupils = current_user.pupils
    return render_template('pupils.html', pupils=users_pupils, back_button_hidden="true")


@app.route('/add_pupil', methods=['GET', 'POST'])
@login_required
def add_pupil():
    form = MakeUserForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('add_pupil.html',
                                   form=form,
                                   message="Пароли не совпадают")
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
        user.set_password(form.password.data)
        user.creator = current_user.id
        print(user)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/pupils')
        # user = db_sess.query(User).filter(User.email == form.email.data).first()
    return render_template('add_pupil.html', back_button_hidden="false", back_url="/pupils",
                           form=form)


@app.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    # print(get('http://localhost:5000/rest_courses/' + str(current_user.id)).json())
    user_courses = get('http://localhost:5000/rest_courses/' + str(current_user.id)).json()[
        "courses"]
    # print(user_courses)
    return render_template('courses.html', courses=user_courses, new_id=len(user_courses) + 1,
                           back_button_hidden='true', back_url='/dictionary')


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
    return render_template('make_course.html', form=form, function="Добавить курс",
                           back_button_hidden='false', back_url="/courses")


@app.route('/add_users_to_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def add_users_to_course(course_id):
    form = AddUsersToCourseForm()
    db_sess = db_session.create_session()
    users = get("http://localhost:5000/rest_users").json()['users']  # f
    # users = db_sess.query(User).filter(User.teacher == 0)
    course = db_sess.query(Courses).get(course_id)
    # print(course)
    pupils = []
    for user in users:
        if not user['teacher']:
            pupil = db_sess.query(User).get(user['id'])
            pupils.append(pupil)
    # print(pupils)
    if form.validate_on_submit():
        pupils = request.form.getlist('lesson_pupil')
        for pupils_id in list(pupils):
            pupil = db_sess.query(User).get(int(pupils_id))
            pupil.courses.append(course)
            db_sess.merge(pupil)
        db_sess.commit()
        # print("redirect")
        return redirect('/courses')
    # print("non validate")
    return render_template('add_users_to_course.html', form=form, pupils=pupils,
                           back_button_hidden='false', back_url="/courses")


@app.route('/courses_delete/<int:course_id>', methods=['GET', 'POST'])
@login_required
def delete_course(course_id):
    ret = delete("http://localhost:5000/rest_course/" + str(course_id)).json()
    if ret == {'success': 'OK'}:
        return redirect("/courses")
    else:
        return abort(404, message=f"Course {course_id} not found")


@app.route('/courses/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course_view(course_id):
    course = get('http://localhost:5000/rest_course/' + str(course_id)
                 ).json()["course"]
    return render_template('course_view.html', course_data=course,
                           back_button_hidden='false', back_url="/courses")


@app.route('/courses/<int:course_id>/lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def lesson_view(course_id, lesson_id):
    lesson = get('http://localhost:5000/rest_lessons/' + str(lesson_id)
                 ).json()["lesson"]
    # print(lesson)
    return render_template('lesson_view.html', lesson_data=lesson, course_id=course_id,
                           back_button_hidden='false', back_url=f"/courses/{course_id}")


@app.route('/make_lesson/<int:course_id>', methods=['GET', 'POST'])
@login_required
def make_lesson(course_id):
    form = LessonsForm()
    db_sess = db_session.create_session()
    current_course = db_sess.query(Courses).get(course_id)
    all_words = db_sess.query(Words).all()
    all_trainers = db_sess.query(Trainers).all()
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
        current_course.lessons.append(new_lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(course_id))
    return render_template('make_lesson.html', form=form, dictionary=all_words,
                           trainers=all_trainers, len_dictionary=len(all_words),
                           len_trainers=len(all_trainers))


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
    # all_words = db_sess.query(Words).all()
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
    return render_template('add_trainers_to_lesson.html', trainers=all_trainers, form=form, len_trainers=len(all_trainers),
                           lesson_trainers=lesson_trainers, unused_trainers=unused_trainers)


@app.route('/add_words_to_lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def add_words_to_lesson(lesson_id):
    form = AddWordsToLessonForm()
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    current_course = 0
    for c in db_sess.query(User).get(current_user.id).courses:
        if lesson in c.lessons:
            current_course = c
    all_words = db_sess.query(Words).all()
    # all_trainers = db_sess.query(Trainers).all()
    lesson_words = lesson.words
    unused_words = sorted(list(set(all_words).difference(set(lesson_words))), key=lambda x: x.id)
    # unused_trainers = sorted(list(set(all_trainers).difference(set(lesson.trainers))),
    #                          key=lambda x: x.id)

    if form.validate_on_submit():
        words = request.form.getlist('lesson_word')
        lesson.words = []
        for word_id in list(words):
            sql_word = db_sess.query(Words).get(int(word_id))
            lesson.words.append(sql_word)
        current_course.lessons.append(lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(current_course.id) + '/lesson/' + str(lesson_id))
    return render_template('add_words_to_lesson.html', lesson_words=lesson_words, unused_words=unused_words,
                           dictionary=all_words, form=form, len_dictionary=len(all_words))


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
    # trainings = ["1 training", "2 training", "3 training"]
    # print(trainings)

    if request.method == "GET":
        form.name.data = lesson.name

    if form.validate_on_submit():
        lesson.name = form.name.data
        current_course.lessons.append(lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(current_course.id) + '/lesson/' + str(lesson_id))

    return render_template('change_lesson_name.html', form=form)
    # return render_template('lesson_view.html', lesson_data=lesson)


@app.route('/courses/<int:course_id>/lesson_delete/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def delete_lesson(course_id, lesson_id):
    ret = delete("http://localhost:5000/rest_lessons/" + str(lesson_id)).json()
    if ret == {'success': 'OK'}:
        return redirect("/courses/" + str(course_id))
    else:
        return abort(404, message=f"Lesson {lesson_id} not found")


@app.route("/delete_word_from_lesson/<int:lesson_id>/<int:word_id>", methods=['GET'])
@login_required
def delete_word_from_lesson(lesson_id, word_id):
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lessons).get(lesson_id)
    # words = [item.to_dict(only=('id', 'hieroglyph', "translation")) for item in list(lesson.words)]
    word = db_sess.query(Words).get(word_id)
    if word in lesson.words:
        lesson.words.remove(word)
        db_sess.merge(lesson)
        db_sess.commit()
        current_course = 0
        for c in db_sess.query(User).get(current_user.id).courses:
            if lesson in c.lessons:
                current_course = c
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


def list_to_javascript(array):
    array_js = []
    for i in range(len(array)):
        word = array[i]
        # print(word)
        array_js.append(";".join([str(word["id"]),
                                  word["hieroglyph"],
                                  word["translation"],
                                  word["front_side"],  # иероглиф
                                  word["left_side"],  # перевод
                                  word["right_side"],  # транскрипция
                                  word["down_side"],  # картинка
                                  word["up_side"],
                                  word["front_side_audio"],
                                  word["up_side_audio"],
                                  word["left_side_audio"],
                                  str(word["author"])]))  # свосочетание
    array_js = ";;;".join(array_js)
    return array_js


@app.route('/dictionary', methods=['GET', 'POST'])
@login_required
def dict_view():
    all_words = get("http://localhost:5000/rest_dict").json()["words"]
    my_words = []
    rest_words = []
    for word in all_words:
        if word["author"] == current_user.id:
            my_words.append(word)
        else:
            rest_words.append(word)
    # all_words = my_words + rest_words
    len_all_words = len(all_words)

    # my_page_number = len(my_words) // 30 + 1
    # rest_page_number = len(rest_words) // 30 + 1
    # all_page_number = len(all_words) // 30 + 1

    # my_words = my_words[30 * (page - 1):30 * page]
    # rest_words = rest_words[30 * (page - 1):30 * page]
    # all_words = all_words[30 * (page - 1):30 * page]

    my_words_js = list_to_javascript(my_words)
    rest_words_js = list_to_javascript(rest_words)
    all_words_js = list_to_javascript(all_words)
    # if len_all_words == 0:
    #     pages_number = 1
    # else:
    #     pages_number = (len_all_words - 1) // 30 + 1
    return render_template("dictionary.html", all_words=all_words, current_user=current_user,
                           len_all_words=len_all_words,
                           my_words=my_words, rest_words=rest_words,
                           my_words_js=my_words_js, rest_words_js=rest_words_js,
                           all_words_js=all_words_js, back_button_hidden="true")


@app.route('/add_word', methods=['GET', 'POST'])
@login_required
def add_word():
    form = WordsForm()
    db_sess = db_session.create_session()
    # db_sess.expire_on_commit = False
    # all_words = db_sess.query(Words).all()
    # 你
    # /static/tutorial_left.png
    front_start_preview = "/static/tutorial_front.png"
    left_start_preview = "/static/tutorial_left.png"
    right_start_preview = "/static/tutorial_right.png"
    up_start_preview = "/static/tutorial_up.png"
    down_start_preview = "/static/tutorial_down.png"
    if form.validate_on_submit():
        new_word = Words()
        new_word.author = current_user.id
        new_word.hieroglyph = form.hieroglyph.data
        new_word.translation = form.translation.data
        print(new_word.hieroglyph)
        print(new_word.translation)
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
        else:
            new_word.front_side = "undefined_image.png"
        if left:
            left.save(filepath + "_left.png")
            new_word.left_side = save_name + "_left.png"
        else:
            new_word.left_side = "undefined_image.png"
        if right:
            right.save(filepath + "_right.png")
            new_word.right_side = save_name + "_right.png"
        else:
            new_word.right_side = "undefined_image.png"
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
        else:
            new_word.up_side = "undefined_image_up.png"
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
        else:
            new_word.down_side = "undefined_image_down.png"

        if transcription_audio:
            transcription_audio.save(filepath + "_trans_audio.mp3")
            new_word.front_side_audio = save_name + "_trans_audio.mp3"
            new_word.right_side_audio = save_name + "_trans_audio.mp3"
            new_word.down_side_audio = save_name + "_trans_audio.mp3"
            # print(new_word.right_side_audio)
        else:
            # print(None)
            new_word.front_side_audio = "undefined_trans_audio.mp3"
            new_word.right_side_audio = "undefined_trans_audio.mp3"
            new_word.down_side_audio = "undefined_trans_audio.mp3"
        if phrase_audio:
            phrase_audio.save(filepath + "_phrase_audio.mp3")
            new_word.up_side_audio = save_name + "_phrase_audio.mp3"
        else:
            new_word.up_side_audio = "undefined_phrase_audio.mp3"
        if translation_audio:
            translation_audio.save(filepath + "_translation_audio.mp3")
            new_word.left_side_audio = save_name + "_translation_audio.mp3"
        else:
            new_word.left_side_audio = "undefined_translation_audio.mp3"
        cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
        cur_user.words.append(new_word)
        db_sess.commit()
        db_sess.close()
        return redirect('/dictionary')
    return render_template('make_word.html', form=form, filename="tmp",
                           front_start_preview=front_start_preview,
                           left_start_preview=left_start_preview,
                           right_start_preview=right_start_preview,
                           up_start_preview=up_start_preview,
                           down_start_preview=down_start_preview)


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
            ret = post("http://localhost:5000/rest_dict", json=data, params=data)
        # print(ret)
        return redirect("/dictionary")
    return redirect("/dictionary")


@app.route('/delete_word/<int:word_id>', methods=['GET', 'POST'])
@login_required
def delete_word(word_id):  # ff
    ret = delete("http://localhost:5000/rest_word/" + str(word_id)).json()
    # print(ret)
    if ret == {'success': 'OK'}:
        return redirect("/dictionary")
    else:
        return ret


@app.route('/dict_word/<int:word_id>', methods=['GET', 'POST'])
@login_required
def dict_word_view(word_id):
    word = get('http://localhost:5000/rest_word/' + str(word_id)).json()["word"]
    # print(word)
    all_words = get("http://localhost:5000/rest_dict").json()["words"]
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
    # front_img = url_for("static", filename=word["front_side"])
    return render_template('word_view.html',
                           front_img=url_for("static", filename=word["front_side"]),
                           left_img=url_for("static", filename=word["left_side"]),
                           right_img=url_for("static", filename=word["right_side"]),
                           up_img=url_for("static", filename=word["up_side"]),
                           down_img=url_for("static", filename=word["down_side"]),
                           front_audio=url_for("static", filename=word["front_side_audio"]),
                           left_audio=url_for("static", filename=word["left_side_audio"]),
                           right_audio=url_for("static", filename=word["right_side_audio"]),
                           up_audio=url_for("static", filename=word["up_side_audio"]),
                           down_audio=url_for("static", filename=word["down_side_audio"]),
                           back_url="/dictionary",
                           dict=all_words,
                           prev_button_visibility=prev_button_visibility,
                           next_button_visibility=next_button_visibility,
                           prev_word_url="http://127.0.0.1:5000/" + "dict_word/" + str(prev_id),
                           next_word_url="http://127.0.0.1:5000/" + "dict_word/" + str(next_id))


@app.route('/courses/<int:course_id>/lesson_word/<int:lesson_id>/word/<int:word_id>',
           methods=['GET', 'POST'])
@login_required
def lesson_word_view(course_id, lesson_id, word_id):
    word = get('http://localhost:5000/rest_word/' + str(word_id)).json()["word"]
    lesson_words = get('http://localhost:5000/rest_lessons/' + str(lesson_id)
                       ).json()["lesson"]["words"]
    # print(lesson_words)
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
                           front_img=url_for("static", filename=word["front_side"]),
                           left_img=url_for("static", filename=word["left_side"]),
                           right_img=url_for("static", filename=word["right_side"]),
                           up_img=url_for("static", filename=word["up_side"]),
                           down_img=url_for("static", filename=word["down_side"]),
                           front_audio=url_for("static", filename=word["front_side_audio"]),
                           left_audio=url_for("static", filename=word["left_side_audio"]),
                           right_audio=url_for("static", filename=word["right_side_audio"]),
                           up_audio=url_for("static", filename=word["up_side_audio"]),
                           down_audio=url_for("static", filename=word["down_side_audio"]),
                           back_url="/courses/" + str(course_id) + "/lesson/" + str(lesson_id),
                           dict=lesson_words,
                           prev_button_visibility=prev_button_visibility,
                           next_button_visibility=next_button_visibility,
                           prev_word_url="http://127.0.0.1:5000/" + "courses/" + str(
                               course_id) + "/lesson_word/" + str(lesson_id) + "/word/" + str(
                               prev_id),
                           next_word_url="http://127.0.0.1:5000/" + "courses/" + str(
                               course_id) + "/lesson_word/" + str(lesson_id) + "/word/" + str(
                               next_id))


@app.route('/courses/<int:course_id>/lesson_word/<int:lesson_id>/trainer/<int:trainer_id>',
           methods=['GET', 'POST'])
@login_required
def lesson_trainer_view(course_id, lesson_id, trainer_id):
    db_sess = db_session.create_session()
    course = db_sess.query(Courses).get(course_id)
    lesson = db_sess.query(Lessons).get(lesson_id)
    trainer = db_sess.query(Trainers).get(trainer_id)
    lesson_words = []
    for i in range(len(lesson.words)):
        word = lesson.words[i]
        lesson_words.append(";".join([word.front_side,  # иероглиф
                                      word.left_side,  # перевод
                                      word.right_side,  # транскрипция
                                      word.down_side,  # картинка
                                      word.up_side,
                                      word.front_side_audio,
                                      word.up_side_audio,
                                      word.left_side_audio]))  # свосочетание
    if len(lesson_words) >= 6:
        answer_button_number = 6
    else:
        answer_button_number = len(lesson_words)
    lesson_words = ";;;".join(lesson_words)
    return render_template('trainer_view.html', course=course, lesson=lesson, trainer=trainer,
                           lesson_words=lesson_words, answer_button_number=answer_button_number,
                           back_url=f"/courses/{course_id}/lesson/{lesson_id}",
                           back_button_hidden="false")


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
    # print(transcription_audio_file)

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
            # print(new_word.right_side_audio)
        # else:
        #     # print(None)
        #     new_word.front_side_audio = "undefined_trans_audio.mp3"
        #     new_word.right_side_audio = "undefined_trans_audio.mp3"
        #     new_word.down_side_audio = "undefined_trans_audio.mp3"
        if phrase_audio:
            phrase_audio.save(filepath + "_phrase_audio.mp3")
            new_word.up_side_audio = save_name + "_phrase_audio.mp3"
        # else:
        #     new_word.up_side_audio = "undefined_phrase_audio.mp3"
        if translation_audio:
            translation_audio.save(filepath + "_translation_audio.mp3")
            new_word.left_side_audio = save_name + "_translation_audio.mp3"
        # else:
        # new_word.left_side_audio = "undefined_translation_audio.mp3"
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
                           phrase_audio_file=phrase_audio_file,
                           translation_audio_file=translation_audio_file,
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
# "GET /word/images/down_0.png HTTP/1.1"
