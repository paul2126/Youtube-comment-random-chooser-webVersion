# from flask_sqlalchemy import SQLAlchemy

# db = SQLAlchemy()           #SQLAlchemy를 사용해 데이터베이스 저장

# class Fcuser(db.Model): 
#     __tablename__ = 'fcuser'   #테이블 이름 : fcuser
#     id = db.Column(db.Integer, primary_key = True)   #id를 프라이머리키로 설정
#     password = db.Column(db.String(64))     #패스워드를 받아올 문자열길이 
#     userid = db.Column(db.String(32))       #이하 위와 동일
#     username = db.Column(db.String(8))



# models.py
from app.extensions import db
from flask_login import UserMixin

class Fcuser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def get_id(self):
        return self.id