from flask import render_template, flash, redirect, url_for
from flask import request
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.forms import JoinGameForm, GameForm, WaitingForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Game, Deck, Ledger, Trick
from werkzeug.urls import url_parse

import datetime
import random
import os
import time

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = current_user
    return render_template('index.html', 
                            title='Partida de tute')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', 
                            title='Register', 
                            form=form)

@app.route('/newgame', methods=['GET'])
@login_required
def newgame():
    '''Create a code for a new game and delete old games'''
    s = list('ABCDEFGHIJKLMNOPQESTUVWXYZ')
    new_code = ''.join(random.sample(s,4))
    g = Game(code=new_code)
    if Game.query.filter_by(code=new_code).count() > 0:
        db.session.delete(g)
    db.session.add(g)
    db.session.commit()

    old_games = [h for h in Game.query.all() if
                        h.timestamp < (datetime.datetime.utcnow() 
                                     - datetime.timedelta(hours=1))
                ]
    if old_games:
        for old_game in old_games:
            [db.session.delete(_) for _ in Ledger.query.filter_by(code=old_game.code).all() if _ != None]
            [db.session.delete(_) for _ in Trick.query.filter_by(code=old_game.code).all() if _ != None]
            db.session.delete(old_game)
        db.session.commit()
    
    if Deck.query.count() < 48:
        current = Deck.query.all()
        [db.session.delete(x) for x in current]

        ranks = [n for n in range(1,13)]
        suits = ['oros', 'espadas', 'copas', 'bastos']
        temp = [db.session.add(Deck(card_rank=r, card_suit=s)) for s in suits for r in ranks]
        db.session.commit()

    #Create entries in Ledger table for this game
    cards = Deck.query.all()
    for c in cards:
        db.session.add(Ledger(code=new_code, card_id=c.id))
    db.session.commit()

    return render_template('newgame.html', 
                            title='New Game', 
                            new_code=new_code)

@app.route('/joingame', methods=['GET', 'POST'])
@login_required
def joingame():
    #TODO
    #instead of redirecting to game page, maybe best to 
    #redirect to a waiting room with a refresh and start button
    form = JoinGameForm()
    if form.validate_on_submit():
        g = Game.query.filter_by(code=form.code.data)
        if g.count() < 1:
            flash('Invalid code')
            return redirect(url_for('joingame'))
        if current_user in g.first().joined:
            #User already playing this game
            return redirect(url_for('game'))
        if g.first().started:
            flash('Sorry, the game has already started')
            return redirect(url_for('joingame'))
        if g.first().joined.count() == 4:
            flash('Already max number of participants joined this game')
            return redirect(url_for('joingame'))

        current_user.join_game(g.first())
        db.session.add(current_user)
        db.session.commit()

        for _ in range(8):
            if Ledger.query.filter_by(code=form.code.data, 
                               user_id = None ).count() > 0:
                Ledger.query.filter_by(id=draw_card(form.code.data)).\
                     update({'user_id': current_user.id})
        db.session.commit()

        trick = Trick(code=form.code.data, user=current_user.id)
        db.session.add(trick)
        db.session.commit()

        return redirect('waitingroom/'+form.code.data)

    return render_template('joingame.html', title='Join Game', form=form)

@app.route('/game/<code>', methods=['GET', 'POST'])
@login_required
def game(code):
    g = Game.query.filter_by(code=code)
    if g.count() < 1 :
        flash('Invalid code')
        return redirect(url_for('joingame'))

    if not g.first().started:
        flash('First someone has to start the game')
        return redirect('/waitingroom/'+ code)

    if current_user not in g.first().participants:
        flash('First you have to join')
        return redirect(url_for('joingame'))

    # Pinta
    if g.first().name == None:
        trump_ledger = Ledger.query.filter_by(id=draw_card(code)).first()
        trump = Deck.query.filter_by(id=trump_ledger.card_id).first()
        Ledger.query.filter_by(id=trump_ledger.id).\
                     update({'trump_id': trump.id})
        Ledger.query.filter_by(id=trump_ledger.id).\
                     update({'trump_suit': trump.card_suit})
        db.session.commit()

        Game.query.filter_by(code=code).\
            update({'name':trump.card_rank + ' de ' + trump.card_suit})
        print('Pinta: ' + trump.card_rank + ' de ' + trump.card_suit)
        db.session.commit()
    else:
        trump_ledger = Ledger.query.filter(Ledger.code==code, Ledger.trump_id != None).first()
        trump = Deck.query.filter_by(id=trump_ledger.card_id).first()

    # First hand
    form = GameForm()

    cards, won_cards = update_card_status(code)

    if form.validate_on_submit():
        if 'Refrescar' in request.form:
            return render_template('game.html', 
                title='Game page', 
                users=g.first().participants.all(),
                cards=cards,
                won_cards=won_cards, 
                trump=trump,
                form=form,
                trick=Trick.query.filter(Trick.code==code).all()
                )
                
        if 'Continuar' in request.form:
            # if this is the last card of this trick
            if Trick.query.filter(Trick.code==code, 
                                    Trick.card == None).count() == 0:
                # For all cards
                # If there are cards with same suit as trump.
                #   Sort them.
                #   Highest wins.
                # else
                #   get cards with same suit as first card. 
                #   Sort them. 
                #   Highest wins.
                        
                tt = sorted(Trick.query.filter(Trick.code==code, 
                                            Trick.suit == trump.card_suit).all())
                print('cartas de la pinta', tt)
                if tt:
                    winner = tt[-1]
                else:
                    suit = Trick.query.filter(Trick.code==code, 
                                            Trick.suit != trump.card_suit).first().suit
                    tt = sorted(Trick.query.filter(Trick.code==code, 
                                            Trick.suit == suit).all())
                    print('cartas del primer palo (', suit,'):', tt)
                    winner = tt[-1]
                print('Winner: ', winner.rank, 'de', winner.suit)

                # from the winner card => winner user
                # Update Ledger (played cards)
                # Update Ledger won cards

                for t in Trick.query.filter_by(code=code).all():
                    print(t)
                    c = Ledger.query.filter_by(code=code,card_id=t.card).first()
                    c.card_played = True
                    c.card_winner = winner.user
                db.session.commit()

                # If no cards left to play, end of the game!
                left_to_play = Ledger.query.filter_by(code=code, card_played=False).all()
                print('current hand', [c.id for c in cards])
                if left_to_play:
                    # new draw for each player
                    for u in g.first().participants:
                        if Ledger.query.filter_by(code=code, 
                               user_id = None ).count() > 0:
                            new_card = Ledger.query.filter_by(id=draw_card(code)).first()
                            print('New card', new_card.card_id)
                            new_card.user_id = u.id
                        db.session.commit()
                    # cards.append(Deck.query.filter_by(id=new_card.card_id).first())
                    # cards.remove(trick_card)
                else:
                    print('end_of the game!')
                    for u in g.first().participants.all():
                        print([Deck.query.filter_by(id=x.card_id).first().card_rank 
                                for x in Ledger.query.filter_by(code=code,
                                            card_winner=u.id).all()])

                print('new hand', [c.id for c in cards])
                # Otherwise reset Trick table and continue

                for c in Trick.query.filter_by(code=code).all():
                    c.card = None
                    c.rank = None
                    c.suit = None
                    c.ledger_id = None
                db.session.commit()
                print('\nstatus of trick after deletion')
                [print(x.id, x.code, x.user, x.card) for x in Trick.query.filter_by(code=code).all()]

        if ' - ' in list(request.form.keys())[-1]:
            card_chosen = request.form
            trick_suit, trick_rank = list(card_chosen.keys())[-1].split(' - ')
            print(trick_rank,'de',trick_suit)
            trick_card = Deck.query.filter(Deck.card_rank == trick_rank,
                                        Deck.card_suit == trick_suit).first()
            trick_ledger = Ledger.query.filter(Ledger.code==code, 
                                            Ledger.user_id == current_user.id,
                                            Ledger.card_id == trick_card.id).first()
            if not trick_ledger.card_played:
                Trick.query.filter(Trick.code==code, Trick.user==current_user.id).\
                                update({'card':trick_card.id,
                                        'rank':trick_card.card_rank,
                                        'suit':trick_card.card_suit,
                                        'ledger_id':trick_ledger.id})
            db.session.commit()
            
            print('status of this trick')
            [print(x.id, x.code, x.user, x.card) for x in Trick.query.filter_by(code=code).all()]

    cards, won_cards = update_card_status(code)

    return render_template('game.html', 
                    title='Game page', 
                    users=g.first().participants.all(),
                    cards=cards,
                    won_cards=won_cards, 
                    trump=trump,
                    form=form,
                    trick=Trick.query.filter(Trick.code==code).all())

@app.route('/waitingroom/<code>', methods=['GET', 'POST'])
@login_required
def waitingroom(code):

    g = Game.query.filter_by(code=code)
    if g.count() < 1 :
        flash('Invalid code')
        return redirect(url_for('joingame'))

    if current_user not in g.first().participants:
        flash('First you have to join')
        return redirect(url_for('joingame'))
    else:
        form = WaitingForm()
        other_users = [u for u in g.first().joined.all() 
                                    if u.username != current_user.username]

        if form.validate_on_submit():
            if 'refresh' in request.form:
                print('refresh')
                return render_template('waitingroom.html', 
                    title='Room '+ code, 
                    users=other_users,
                    form=form)

            elif 'start' in request.form:
                print('start')
                Game.query.filter_by(code=code).\
                    update({'started': True})
                db.session.commit()

                return redirect('/game/'+code)
        
        return render_template('waitingroom.html', 
            title='Room '+ code, 
            users=other_users,
            form=form)

def draw_card(code):
    '''Return a card from those still available, but not 
    the trump unless it is the last card
    '''
    available_cards = Ledger.query.filter_by(code=code, 
                               user_id = None ).all()
    t = Ledger.query.filter(Ledger.code == code, 
                             Ledger.trump_id != None).first()
    if t != None:
        available_cards.remove(t)
    temp = [c.id for c in available_cards]
    random.shuffle(temp)
    if len(temp) == 0:
        return t.id
    else:
        return random.choice(temp)

def update_card_status(code):
    #update status or cards
    my_cards = Ledger.query.filter_by(code=code, 
                               user_id=current_user.id,
                               card_played=False ).all()
    cards = list()
    for c in my_cards:
        temp = Deck.query.filter_by(id=c.card_id).first()
        cards.append(temp)
    cards = sorted(cards)

    my_won_cards = Ledger.query.filter_by(code=code, 
                               card_winner=current_user.id,
                               card_played=True ).all()
    won_cards = list()
    for c in my_won_cards:
        temp = Deck.query.filter_by(id=c.card_id).first()
        won_cards.append(temp)
    won_cards = sorted(won_cards)
    print('Won cards: ',won_cards)
    return cards, won_cards