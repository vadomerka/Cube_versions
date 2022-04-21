from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired


class LinkForm(FlaskForm):
    link_field = StringField('Ссылка на курс', validators=[DataRequired()])
    submit = SubmitField('Перейти')
