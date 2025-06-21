from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def enable_sqlite_fk_constraints(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    hobby = db.Column(db.String(100))         # 趣味
    mbti = db.Column(db.String(10))           # MBTI
    message = db.Column(db.String(255)) 
    
    icon_filename = db.Column(db.String(120), default='default.png')       # 一言メッセージ

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    body = db.Column(db.String(140), nullable=False)
    good_count = db.Column(db.Integer, default=0)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user=db.relationship("User", backref="tweets")


    comments=db.relationship(
        "Comment", 
        backref="tweet", 
        lazy=True,
        cascade="all, delete-orphan"
    )

class TweetGoodUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # リレーション
    tweet_id = db.Column(
        db.Integer, 
        db.ForeignKey('tweet.id', ondelete='CASCADE'), 
        nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # 逆参照（必要なら）
    
    user = db.relationship('User', backref=db.backref('comments', lazy=True))

