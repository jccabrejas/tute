from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, EqualTo
from app.models import User
#TODO
#from app.models import GameCode
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

class LoginForm(FlaskForm):
    username = StringField('Alias', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    family_secret = PasswordField('Secret', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_family_secret(self, family_secret):
        if self.family_secret.data != Config().SECRET_KEY:
            raise ValidationError('Check with web owner')


class JoinGameForm(FlaskForm):
    code = StringField('Game Code', validators=[DataRequired()])
    join_game = SubmitField('Join Game')
  
    #TODO check that code exists in database

class GameForm(FlaskForm):
    card_1 = SubmitField('Card 1')
    card_2 = SubmitField('Card 2')
    card_3 = SubmitField('Card 3')
    card_4 = SubmitField('Card 4')
    card_5 = SubmitField('Card 5')
    card_6 = SubmitField('Card 6')
    card_7 = SubmitField('Card 7')
    card_8 = SubmitField('Card 8')

class WaitingForm(FlaskForm):
    refresh = SubmitField('Refresh')
    start = SubmitField('Start')
