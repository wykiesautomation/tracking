import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from .models import db,User,seed_demo
login=LoginManager();login.login_view='main.login';csrf=CSRFProtect()
@login.user_loader
def load_user(uid):return db.session.get(User,int(uid))
def create_app(testing=False):
 app=Flask(__name__);uri=os.getenv('DATABASE_URL','sqlite:///fleettrack360.db').replace('postgres://','postgresql+psycopg://',1)
 app.config.update(SECRET_KEY=os.getenv('SECRET_KEY','fleettrack-local'),SQLALCHEMY_DATABASE_URI=uri,SQLALCHEMY_TRACK_MODIFICATIONS=False,TESTING=testing,WTF_CSRF_ENABLED=not testing,MAX_CONTENT_LENGTH=8*1024*1024,MAP_TILE_URL=os.getenv('MAP_TILE_URL','https://tile.openstreetmap.org/{z}/{x}/{y}.png'),MAP_ATTRIBUTION=os.getenv('MAP_ATTRIBUTION','&copy; OpenStreetMap contributors'),MAP_MAX_ZOOM=int(os.getenv('MAP_MAX_ZOOM','19')))
 db.init_app(app);login.init_app(app);csrf.init_app(app)
 from .routes import bp
 from .api import api
 app.register_blueprint(bp);app.register_blueprint(api,url_prefix='/api/fleet/v1');csrf.exempt(api)
 with app.app_context():
  db.create_all()
  if os.getenv('SEED_DEMO','false').lower()=='true':seed_demo()
 return app
