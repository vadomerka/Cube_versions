from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from wtforms.fields import EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class CoursesForm(FlaskForm):
    name = StringField('Название курса', validators=[DataRequired(), Length(min=1, max=32,
                                                                            message="Название курса должно быть короче 32 символов")])
    about = TextAreaField("Описание", validators=[
        Length(min=0, max=512, message="Описание курса должно быть короче 512 символов")])
    submit = SubmitField('Применить')


class AddItemToSomethingForm(FlaskForm):
    # name = StringField('Название курса', validators=[DataRequired(), Length(min=1, max=20, message="Название курса должно быть короче 20 символов")])
    submit = SubmitField('Применить')
