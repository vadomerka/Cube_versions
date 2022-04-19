from flask import Flask, render_template, redirect, url_for
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
from resourses.dict_resourses import WordResourse
from resourses.lesson_resourses import LessonResource
from flask_restful import Api
from requests import get, post, delete, put
import os
from PIL import Image

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api.add_resource(CourseListResource, '/rest_courses/<int:user_id>')
api.add_resource(CourseResource, '/rest_courses/<int:user_id>/<int:course_id>')
api.add_resource(DictResourse, "/rest_dict")
api.add_resource(WordResourse, "/rest_word/<int:word_id>")
api.add_resource(LessonResource, "/rest_lessons/<int:lesson_id>")
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
            about=form.about.data,
            teacher=form.teacher.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        return redirect('/login')
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


@app.route('/adress')
def adress():
    coords = get_coords_of_address('Москва, пр-т Вернадского, 86с2')
    address_ll = ",".join(coords)
    map_file = "static/map.png"
    map_request = f"http://static-maps.yandex.ru/1.x/?ll={coords[0]},{coords[1]}&z=16&l=sat"
    response=requests.get(map_request)
    with open(map_file, "wb") as file:
        file.write(response.content)
        return render_template('adress.html')


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
    return render_template('make_course.html', form=form, function="Добавить курс")


@app.route('/make_lesson/<int:course_id>', methods=['GET', 'POST'])
@login_required
def make_lesson(course_id):
    form = LessonsForm()
    db_sess = db_session.create_session()
    current_course = db_sess.query(Courses).get(course_id)
    all_words = db_sess.query(Words).all()
    if form.validate_on_submit():
        new_lesson = Lessons()
        new_lesson.name = form.name.data
        words = request.form.getlist('lesson_word')
        for word_id in list(words):
            sql_word = db_sess.query(Words).get(int(word_id))
            new_lesson.words.append(sql_word)
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


@app.route('/courses/<int:course_id>/lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def lesson_view(course_id, lesson_id):
    lesson = get('http://localhost:5000/rest_lessons/' + str(lesson_id)
                 ).json()["lesson"]
    # print(lesson)
    return render_template('lesson_view.html', lesson_data=lesson, course_id=course_id)


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
    all_words = db_sess.query(Words).all()
    if request.method == "GET":
        form.name.data = lesson.name
    if form.validate_on_submit():
        lesson.name = form.name.data
        words = request.form.getlist('lesson_word')
        for word_id in list(words):
            sql_word = db_sess.query(Words).get(int(word_id))
            lesson.words.append(sql_word)
        current_course.lessons.append(lesson)
        db_sess.merge(current_course)
        db_sess.commit()
        return redirect('/courses/' + str(current_course.id) + '/lesson/' + str(lesson_id))
    return render_template('make_lesson.html', form=form, dictionary=all_words)
    # return render_template('lesson_view.html', lesson_data=lesson)


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
    return 404


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
    # db_sess.expire_on_commit = False
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
        transcription_audio = request.files['transcription_audio']
        phrase_audio = request.files['phrase_audio']
        path_to_file = os.path.dirname(__file__)
        full_path = os.path.join(path_to_file)
        filepath = os.path.join(full_path, "static", str(new_word.author))
        if front:
            front.save(filepath + "_front.png")
            new_word.front_side = str(new_word.author) + "_front.png"
        if left:
            left.save(filepath + "_left.png")
            new_word.left_side = str(new_word.author) + "_left.png"
        if right:
            right.save(filepath + "_right.png")
            new_word.right_side = str(new_word.author) + "_right.png"
        if up:
            up.save(filepath + "_up_0.png")
            new_word.up_side = str(new_word.author) + "_up.png"
            im = Image.open(filepath + "_up_0.png")
            im = im.transpose(Image.ROTATE_90)
            im.save(filepath + "_up_90.png")
            im = im.transpose(Image.ROTATE_90)
            im.save(filepath + "_up_180.png")
            im = im.transpose(Image.ROTATE_90)
            im.save(filepath + "_up_270.png")
        if down:
            down.save(filepath + "_down_0.png")
            new_word.down_side = str(new_word.author) + "_down.png"
            im = Image.open(filepath + "_down_0.png")
            im = im.transpose(Image.ROTATE_270)
            im.save(filepath + "_down_90.png")
            im = im.transpose(Image.ROTATE_270)
            im.save(filepath + "_down_180.png")
            im = im.transpose(Image.ROTATE_270)
            im.save(filepath + "_down_270.png")
        if transcription_audio:
            transcription_audio.save(filepath + "_trans_audio.mp3")
            new_word.right_side_audio = str(new_word.author) + "_trans_audio.mp3"
            # print(new_word.right_side_audio)
        else:
            print(None)
        if phrase_audio:
            phrase_audio.save(filepath + "_phrase_audio.mp3")
            new_word.up_side_audio = str(new_word.author) + "_phrase_audio.mp3"
        else:
            print(None)
        cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
        cur_user.words.append(new_word)
        db_sess.commit()
        db_sess.close()
        return redirect('/dictionary')
    return render_template('make_word.html', form=form, dictionary=all_words, filename="tmp")


@app.route('/delete_word/<int:word_id>', methods=['GET', 'POST'])
@login_required
def delete_word(word_id):
    ret = delete("http://localhost:5000/rest_word/" + str(word_id)).json()
    # print(ret)
    if ret == {'success': 'OK'}:
        return redirect("/dictionary")
    else:
        return "что-то пошло не так"


@app.route('/word/<int:word_id>', methods=['GET', 'POST'])
@login_required
def word_view(word_id):
    word = get('http://localhost:5000/rest_word/' + str(word_id)).json()["word"]
    # print(word)

    return render_template('dict_word.html',
                           front_img=url_for("static", filename=word["front_side"]),
                           left_img=url_for("static", filename=word["left_side"]),
                           right_img=url_for("static", filename=word["right_side"]),
                           up_img=url_for("static", filename=word["up_side"]),
                           down_img=url_for("static", filename=word["down_side"]),
                           # front_audio=url_for("static", filename=word["front_side_audio"]),
                           right_audio=url_for("static", filename=word["right_side_audio"]),
                           up_audio=url_for("static", filename=word["up_side_audio"]),
                           back_url="/dictionary",
                           dict="")


# /change_word/1
@app.route('/change_word/<int:word_id>', methods=['GET', 'POST'])
@login_required
def change_word(word_id):
    form = WordsForm()
    db_sess = db_session.create_session()
    all_words = db_sess.query(Words).all()
    new_word = db_sess.query(Words).get(word_id)
    path_to_file = os.path.dirname(__file__)
    full_path = os.path.join(path_to_file)
    filepath = os.path.join(full_path, "static", str(current_user.id))

    # form.hieroglyph.data = new_word.hieroglyph
    # form.translation.data = new_word.translation
    # request.files['front'] = Image.open(filepath + "_front.png")
    # request.files['left'] = Image.open(filepath + "_left.png")
    # request.files['right'] = Image.open(filepath + "_right.png")
    # request.files['up'] = Image.open(filepath + "_up.png")
    # request.files['down'] = Image.open(filepath + "_down.png")
    # request.files['transcription_audio'] = Image.open(filepath + "_trans_audio.mp3")
    # request.files['phrase_audio'] = Image.open(filepath + "_phrase_audio.mp3")
    if form.validate_on_submit():
        new_word = Words()
        new_word.author = current_user.id
        new_word.hieroglyph = form.hieroglyph.data
        new_word.translation = form.translation.data
        front = request.files['front']
        # print(request.files['front'])
        left = request.files['left']
        right = request.files['right']
        up = request.files['up']
        down = request.files['down']
        transcription_audio = request.files['transcription_audio']
        phrase_audio = request.files['phrase_audio']
        path_to_file = os.path.dirname(__file__)
        full_path = os.path.join(path_to_file)
        filepath = os.path.join(full_path, "static", str(new_word.author))
        if front:
            front.save(filepath + "_front.png")
            new_word.front_side = str(new_word.author) + "_front.png"
        if left:
            left.save(filepath + "_left.png")
            new_word.left_side = str(new_word.author) + "_left.png"
        if right:
            right.save(filepath + "_right.png")
            new_word.right_side = str(new_word.author) + "_right.png"
        if up:
            up.save(filepath + "_up_0.png")
            new_word.up_side = str(new_word.author) + "_up.png"
            im = Image.open(filepath + "_up_0.png")
            im = im.transpose(Image.ROTATE_90)
            im.save(filepath + "_up_90.png")
            im = im.transpose(Image.ROTATE_90)
            im.save(filepath + "_up_180.png")
            im = im.transpose(Image.ROTATE_90)
            im.save(filepath + "_up_270.png")
        if down:
            down.save(filepath + "_down_0.png")
            new_word.down_side = str(new_word.author) + "_down.png"
            im = Image.open(filepath + "_down_0.png")
            im = im.transpose(Image.ROTATE_270)
            im.save(filepath + "_down_90.png")
            im = im.transpose(Image.ROTATE_270)
            im.save(filepath + "_down_180.png")
            im = im.transpose(Image.ROTATE_270)
            im.save(filepath + "_down_270.png")
        if transcription_audio:
            transcription_audio.save(filepath + "_trans_audio.mp3")
            new_word.right_side_audio = str(new_word.author) + "_trans_audio.mp3"
            # print(new_word.right_side_audio)
        else:
            print(None)
        if phrase_audio:
            phrase_audio.save(filepath + "_phrase_audio.mp3")
            new_word.up_side_audio = str(new_word.author) + "_phrase_audio.mp3"
        else:
            print(None)
        cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
        cur_user.words.append(new_word)
        db_sess.commit()
        db_sess.close()
        return redirect('/dictionary')
    return render_template('make_word.html', form=form, dictionary=all_words, filename="tmp")


def get_coords_of_address(address):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": address,
        "format": "json"
    }

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if not response:
        return None

    json_response = response.json()
    toponym = json_response["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]
    toponym_coodrinates = toponym["Point"]["pos"]
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
    return toponym_longitude, toponym_lattitude


def main():
    db_session.global_init("db/users.db")
    app.run()


if __name__ == '__main__':
    main()
# "GET /word/images/down_0.png HTTP/1.1"
