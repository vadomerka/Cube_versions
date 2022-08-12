from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from wtforms.fields import EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class WordsForm(FlaskForm):
    hieroglyph = StringField('Иероглиф', validators=[DataRequired(), Length(min=0, max=32)])
    translation = StringField('Перевод', validators=[DataRequired(), Length(min=0, max=32)])
    transcription = StringField('Транскрипция', validators=[DataRequired(), Length(min=0, max=32)])
    phrase_ch = StringField('Словосочетание', validators=[DataRequired(), Length(min=0, max=32)])
    phrase_ru = StringField('Перевод словосочетания', validators=[DataRequired(), Length(min=0, max=32)])
    submit = SubmitField('Применить')

