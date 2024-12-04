from flask import Flask
from flask_login import LoginManager
import os #절대경로를 지정하기 위한 Os모듈 임포트
from app.extensions import db, login_manager, csrf

from app.models import Fcuser
import configparser

config = configparser.ConfigParser()
config.read("config.ini")
SECRET_KEY = config["APP"]["SECRET_KEY"]

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY 
    basedir = os.path.abspath(os.path.dirname(__file__)) #db파일을 절대경로로 생성
    dbfile = os.path.join(basedir, 'db.sqlite')#db파일을 절대경로로 생성

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + dbfile   
#sqlite를 사용함. (만약 mysql을 사용한다면, id password 등... 더 필요한게많다.)
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True 
#사용자 요청의 끝마다 커밋(데이터베이스에 저장,수정,삭제등의 동작을 쌓아놨던 것들의 실행명령)을 한다.
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
#수정사항에 대한 track을 하지 않는다. True로 한다면 warning 메시지유발
    
    from .routes import main
    app.register_blueprint(main)
    
    csrf.init_app(app)

    with app.app_context():
        db.init_app(app)
        db.app = app
        db.create_all()  #db 생성

    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        return Fcuser.query.get(int(user_id))

    return app
