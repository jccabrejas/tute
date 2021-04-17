from datetime import datetime
from collections import namedtuple
from random import shuffle

from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

Card = namedtuple('Card', ['rank', 'suit'])

class SpanishDeck:
    ranks = [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 3, 1]
    suits = ['oros', 'espadas', 'copas', 'bastos']

    def __init__(self):
        self._cards = [Card(rank, suit) 
                        for suit in self.suits 
                        for rank in self.ranks]
        shuffle(self._cards)

    def __len__(sef):
        return len(self._cards)

    def __getitem__(self, position):
        return self._cards[position]

    def __repr__(self):
        return '<Deck with {} cards>'.format(len(self._cards))

    def set_card(self, position, card):
        self._cards[position] = card

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def start_playing(self, game):
        self.game_id = game.id

    def join_game(self, game):
        self.game_id = game.id


    def stop_playing(self, game):
        self.game_id = -1

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Game(db.Model):
    '''
    name: name of the trump
    code: to have different concurrent games
    joined: users which have entered the game code
    participants: User which have pressed the start button in waiting room
    started: True if the last of the participants has pressed start
    next_player:
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    code = db.Column(db.String(4), index=True, unique=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    joined = db.relationship('User', backref='joined', lazy='dynamic')
    #TODO
    # #this actually does not work, as joined and participants will be
    #the same. When you update one, the other is updated
    participants = db.relationship('User', backref='playing', lazy='dynamic')
    started = db.Column(db.Boolean, default=False)
    next_player = db.Column(db.Integer)

    def __repr__(self):
        return '<Game {} - {}>'.format(self.code, self.timestamp)
    
    def add_user(self, user):
        return user.start_playing(self)
    
    def remove_user(self,user):
        return user.stop_playing(self)
    
    def reset(self):
        if self.participants.count() > 0:
            for u in self.participants:
                self.remove_user(u)

class Ledger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4), index=True)
    user_id = db.Column(db.Integer)
    card_id = db.Column(db.Integer)
    card_played = db.Column(db.Boolean, default=False)
    card_winner = db.Column(db.Integer)
    next_player = db.Column(db.Integer)
    trump_id = db.Column(db.Integer)
    trump_suit = db.Column(db.String(7))

class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_suit = db.Column(db.String(7))
    card_rank = db.Column(db.String(2))
    card_text = db.Column(db.String(50))
    card_value = db.Column(db.Integer)
    card_image = db.Column(db.String(50))

    def __lt__(self, other):
        if self.id < other.id:
            return True
        else:
            return False

class Trick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4), index=True)
    user = db.Column(db.Integer)
    card = db.Column(db.Integer)
    suit = db.Column(db.String(7))
    rank = db.Column(db.String(2))
    ledger_id  = db.Column(db.Integer)

    def __lt__(self, other):
        VALUE_MAP = {1:11, 3:10, 12:4, 11:3, 10:2,
             2:-6, 4:-5, 5:-4, 6:-3, 7:-2, 8:-1, 9:0}
        # only valid for cards of same suit
        if VALUE_MAP[int(self.rank)] < VALUE_MAP[int(other.rank)]:
            return True
        else:
            return False