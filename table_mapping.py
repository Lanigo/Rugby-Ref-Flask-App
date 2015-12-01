from sqlalchemy import Column, Integer, create_engine, Text, String, Date, ForeignKey  
from sqlalchemy.ext.declarative import declarative_base  
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import Form
from wtforms import TextField, PasswordField
from wtforms.validators import InputRequired, EqualTo 

Base = declarative_base()  

class Referee(Base):  
    __tablename__ = 'referees'
    id = Column(Integer, primary_key=True)
    f_name = Column(String(50), nullable=False)
    l_name = Column(String(50), nullable=False)
    country = Column(String(50), nullable=False)
    number = Column(Integer, nullable=False)
    years_active = Column(Integer, nullable=False)
    games_reffed = Column(Integer, nullable=False, default=0)
    added_by = Column(String(50), nullable=False)
    total_penalties = Column(Integer, ForeignKey("games.penalties_total"), nullable=False, default=0)
	
class Game(Base):  
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    first_team = Column(String(100), nullable=False)
    second_team = Column(String(100), nullable=False)
    first_score = Column(Integer, nullable=False)
    second_score = Column(Integer, nullable=False)
    active_ref_id = Column(Integer, ForeignKey("referees.id"), nullable=False)
    penalties_total = Column(Integer,  nullable=False)
    games_reffed = Column(String, nullable=False, default=0)
    added_by = Column(String(50), nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    pwdhash = Column(String())
    
    def __init__(self, username, password):
        self.username = username
        self.pwdhash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)

    def is_authenticated(self):
        return True      
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return unicode(self.id) 

class RegistrationForm(Form):
    username = TextField('Username', [InputRequired()])
    password = PasswordField('Password', [InputRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', [InputRequired()])
    
class LoginForm(Form):
    username = TextField('Username', [InputRequired()])
    password = PasswordField('Password', [InputRequired()]) 
	
engine = create_engine('sqlite:///rugbyref.db')

Base.metadata.create_all(engine)
