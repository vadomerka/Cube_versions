from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from wtforms.fields import EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class LessonsForm(FlaskForm):
    name = StringField('Название урока',
                       validators=[DataRequired(), Length(max=32,
                                                          message="Название урока не должно превышать 32 символов")])
    submit = SubmitField('Применить')


class AddSomethingToLessonForm(FlaskForm):
    submit = SubmitField('Применить')
