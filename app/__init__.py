from flask import Flask
import os #절대경로를 지정하기 위한 Os모듈 임포트
from app.extensions import db, login_manager, csrf

from app.models import Fcuser
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'db.sqlite')
    os.environ['FLASK_APP'] = config['FLASK']['FLASK_APP']
    os.environ['FLASK_ENV'] = config['FLASK']['FLASK_ENV']
    app.config['SECRET_KEY'] = config["FLASK"]["SECRET_KEY"] 
    app.config['SQLALCHEMY_DATABASE_URI'] = config['APP']['SQLALCHEMY_DATABASE_URI'] + db_path
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = config['APP']['SQLALCHEMY_COMMIT_ON_TEARDOWN'] 
#사용자 요청의 끝마다 커밋(데이터베이스에 저장,수정,삭제등의 동작을 쌓아놨던 것들의 실행명령)을 한다.
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config['APP']['SQLALCHEMY_TRACK_MODIFICATIONS'] 
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
