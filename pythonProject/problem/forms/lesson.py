from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from wtforms.fields import EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class LessonsForm(FlaskForm):
    name = StringField('Название урока',
                       validators=[DataRequired(), Length(max=40,
                                                          message="Название урока не должно превышать 40 символов")])
    submit = SubmitField('Применить')
