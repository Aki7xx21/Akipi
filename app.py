from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    body = db.Column(db.String(140), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))

@login_manager.user_loader
def load_user(user_id):
     return User.query.get(int(user_id))

@app.route('/')
def top():
    return redirect('/tweets')


@app.route('/tweets/new', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        # POSTメソッドの時の処理。
        title = request.form.get('title')
        body = request.form.get('body')

        tweet = Tweet(title=title, body=body)
        # DBに値を送り保存する
        db.session.add(tweet)
        db.session.commit()
        return redirect('/')
    else:
        # GETメソッドの時の処理
        return render_template('tweets/new.html')
    
@app.route('/tweets')
def index():
    tweets = Tweet.query.all()
    return render_template('tweets/index.html',tweets = tweets)

@app.route('/tweets<int:id>/edit',methods=['GET','POST'])
def update(id):
    tweet = Tweet.query.get(id)
    if request.method == 'GET':
        return render_template('edit.html',post=tweet)
    else:
        tweet.title = request.form.get('title')
        tweet.body = request.form.get('body')
        db.session.commit()
        return redirect('/')
    
@app.route('/tweets<int:id>/delete',methods=['GET'])
def delete(id):
    tweet = Tweet.query.get(id)
    #投稿を削除
    db.session.delete(tweet)
    #削除を反映
    db.session.commit()
    return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
     if request.method == "POST":
         username = request.form.get('username')
         password = request.form.get('password')
         # Userのインスタンスを作成
         user = User(username=username, password=generate_password_hash(password, method='sha256'))
         db.session.add(user)
         db.session.commit()
         return redirect('login')
     else:
         return render_template('signup.html')
     
@app.route('/login', methods=['GET', 'POST'])
def login():
     if request.method == "POST":
         username = request.form.get('username')
         password = request.form.get('password')
         # Userテーブルからusernameに一致するユーザを取得
         user = User.query.filter_by(username=username).first()
         if check_password_hash(user.password, password):
             login_user(user)
             return redirect('/tweets')
     else:
         return render_template('login.html')
     
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('login')

if __name__ == '__main__':
    app.run(debug=True)
