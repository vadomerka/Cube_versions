from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from wtforms.fields import EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired


class WordsForm(FlaskForm):
    hieroglyph = StringField('Иероглиф', validators=[DataRequired()])
    translation = StringField('Перевод', validators=[DataRequired()])
    submit = SubmitField('Применить')

