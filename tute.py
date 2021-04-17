from app import app, db
from app.models import User, Game, Deck, Ledger, Trick

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 
            'User': User, 
            'Game': Game, 
            'Deck': Deck,
            'Ledger': Ledger,
            'Trick': Trick,
            }