from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from wtforms.fields import EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class MakeUserForm(FlaskForm):
    email = EmailField('Почта пользователя', validators=[DataRequired("Пожалуйста, введите вашу почту")])
    name = StringField('Имя пользователя', validators=[Length(min=0, max=32)])
    last_name = StringField('Фамилия пользователя', validators=[Length(min=0, max=32)])
    patronymic = StringField('Отчество пользователя', validators=[Length(min=0, max=32)])
    teacher = BooleanField('Пользователь является учителем?')
    about = StringField('О пользователе', validators=[Length(min=0, max=512)])

    submit = SubmitField('Создать')


class MakePasswordForm(FlaskForm):
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Сохранить пароль')


class LoginForm(FlaskForm):
    email = EmailField('Введите почту', validators=[DataRequired()])
    password = PasswordField('Введите пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
