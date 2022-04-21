from flask import Flask, request, render_template, redirect
from data import db_session
from data.users import User
from forms.user import RegisterForm
from forms.link import LinkForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/link_to_course', methods=['GET', 'POST'])
def link_to_course():
    form = LinkForm()
    if form.validate_on_submit():
        return redirect("/" + form.link_field.data)
        # return render_template('link_to_course.html', form=form, message=form.link_field.data,
        #                        link=form.link_field.data)
    return render_template('link_to_course.html', form=form)


@app.route('/linked', methods=['GET', 'POST'])
def linked():
    print("here")
    return render_template('linked.html')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
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
        print(user)
        # user_dt = db_sess.extend_existing=True
        return redirect('/courses', params={user_data: user_dt})
    return render_template('register.html', title='Регистрация', form=form)


# response = requests.get('https://pythonexamples.org/', params=params)
@app.route('/login', methods=['GET', 'POST'])
def login():
    return redirect("/register")


@app.route('/courses', methods=['GET', 'POST'])
def courses():
    user_corses = db_sess.query(User).all()
    return render_template('courses.html', title='Ваши курсы')


def main():
    db_session.global_init("db/users.db")
    app.run()


if __name__ == '__main__':
    main()
