import os, json, datetime  
from sqlite3 import dbapi2 as sqlite3  
from flask import Flask, request, g, redirect, url_for, render_template, flash, session
from flask.ext.login import LoginManager, login_required, current_user, login_user, logout_user
from table_mapping import *
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker  
from sqlalchemy.orm.exc import NoResultFound 

# create the flask app
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(  
    DEBUG=False,
    SECRET_KEY=''
))

login_manager = LoginManager() 
login_manager.init_app(app) 
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return g.db.query(User).get(int(id))

@app.before_request
def get_current_user():
    g.user = current_user 

@app.before_request
def before_request():  
    print "starting request"
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    g.db = session

@app.teardown_appcontext
def close_db(error):  
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if session.get('username'):
        flash('Your are already logged in.', 'info')
        return redirect(url_for('home'))
    
    form = RegistrationForm(request.form)
    
    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')
        existing_username = g.db.query(User).filter_by(username=username).first()
        if existing_username:
            flash('This username has been already taken. Try another one.', 'warning')
            return render_template('register.html', form=form)
        user = User(username, password)
        g.db.add(user)
        g.db.commit()
        flash('You are now registered. Please login.', 'success')
        return redirect(url_for('home'))
    if form.errors:
        flash(form.errors, 'danger')
                                
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if current_user.is_authenticated():
        flash('You are already logged in.')
        return redirect(url_for('home'))
 
    if request.method == 'POST' and form.validate():
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = g.db.query(User).filter_by(username=username).first()
                                
        if not (existing_user and existing_user.check_password (password)):
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', form=form)
        login_user(existing_user)
        flash('You have successfully logged in.', 'success')
        return redirect(url_for('home'))
    
    if form.errors:
        flash(form.errors, 'danger')
                                
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home')) 
	
@app.route('/show_referees')
def show_referees():  
    """Gets a list of currently registered referees"""
    referees = g.db.query(Referee).all()
    # update the number of games each has reffed
    update_game_counts(referees)
    update_penalty_counts(referees)
    return render_template('show_refs.html', referees=referees)

def update_game_counts(referees):  
    for ref in referees:
        ref.games_reffed = g.db.query(Game).filter(Game.active_ref_id == ref.id).count()
    g.db.commit()

def update_penalty_counts(referees):
        total_penalties = g.db.query(func.sum(Game.penalties_total)).filter(Referee.id == "ref.id").scalar()
        g.db.commit()

@app.route('/ref_info')
def get_ref():  
    """Gets specific info for a ref based on their ID"""
    id = request.args.get('id')
    try:
        ref = g.db.query(Referee).filter_by(id=id).one()
    except NoResultFound:
        print "No result found for {0}".format(id)
        ref = None
    return render_template('ref_info.html', ref=ref)


@app.route('/add_a_ref')
@login_required
def add_a_ref():  
    """Used to render the Add a Referee template"""
    return render_template('add_ref.html')


@app.route('/add_ref', methods=['POST'])
def add_ref():  
    """Adds a given referee to the database"""
    g.db.add(Referee(f_name=request.form['f_name'], l_name=request.form['l_name'],
                     country=request.form['country'],number=request.form['number'],
                     years_active=request.form['years'], added_by=request.form['added']))
    g.db.commit()
    flash('New ref was successfully posted')
    return redirect(url_for('show_referees'))

@app.route('/show_games')
def show_games():  
    """Gets a list of currently played games"""
    referees = g.db.query(Referee).all()
    games = g.db.query(Game).all()
    return render_template('show_games.html', games=games, referees=referees)

@app.route('/add_a_game')
@login_required
def add_a_game():  
    """Used to render the Add a Game template"""
    referees = g.db.query(Referee).all()
    return render_template('add_game.html', referees=referees)


@app.route('/add_game', methods=['POST'])
def add_game():  
    """Used to add a new game record to the database"""
    g.db.add(Game(date=datetime.datetime.strptime(
        request.form['date'], '%Y-%m-%d').date(), first_team=request.form['first_team'],
        second_team=request.form['second_team'], first_score=request.form['first_score'],
        second_score=request.form['second_score'], active_ref_id=request.form['refId'],
                  penalties_total=request.form['penalties_total'], added_by=request.form['added']))
    ref = g.db.query(Referee).filter_by(id=request.form["refId"]).one()
    ref.games_reffed = 1
    foo = request.form['penalties_total']
    ref.total_penalties = ref.total_penalties + int(foo)
    g.db.commit()
    flash('New game was successfully posted')
    return redirect(url_for('show_games'))


@app.route('/edit_game', methods=['POST'])
@login_required
def edit_game():  
    """Edit an existing game's details"""
    game = g.db.query(Game).filter_by(id=request.form['gameid']).one()
    game.first_team = request.form['first_team']
    game.second_team = request.form['second_team']
    game.date = datetime.datetime.strptime(
        request.form['date'], '%Y-%m-%d').date()
    game.first_score = request.form['first_score']
    game.second_score = request.form['second_score']
    game.penalties_total = request.form['penalties_total']
    g.db.commit()
    flash('Game edited!')
    return redirect(url_for('show_games'))


@app.route('/delete_game', methods=['POST'])
@login_required
def delete_game():  
    """Delete an existing game from the database via its ID"""
    game = g.db.query(Game).filter_by(id=request.form['gameid']).one()
    g.db.delete(game)
    g.db.commit()
    flash('Game deleted!')
    return redirect(url_for('show_games'))

@app.route('/game_info', methods=['GET', 'POST'])
def game_info():  
    """Return the details of a game in JSON"""
    gameid = request.args["gameid"]
    game = g.db.query(Game).filter_by(id=gameid).one()
    return json.dumps(dict(id=game.id, date=str(game.date), first_team=game.first_team,
                           second_team=game.second_team, first_score=game.first_score,
                           second_score=game.second_score, penalties_total=game.penalties_total))
	
app.run()
