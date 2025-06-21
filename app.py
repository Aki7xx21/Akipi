from flask import Flask,render_template,request,redirect,jsonify,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Tweet, TweetGoodUser, User, Comment
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = os.urandom(24)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view="login"


@login_manager.user_loader
def load_user(user_id):
     return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template("home.html")


@app.route('/tweets/new', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        # POSTメソッドの時の処理。
        title = request.form.get('title')
        body = request.form.get('body')

        tweet = Tweet(title=title, body=body, user_id=current_user.id)
        # DBに値を送り保存する
        db.session.add(tweet)
        db.session.commit()
        return redirect('/tweets')
    else:
        # GETメソッドの時の処理
        return render_template('tweets/new.html')

@app.route('/tweets')
@login_required
def tweets():
    tweets = Tweet.query.all()
    for tweet in tweets:
        print(tweet.user.username, tweet.user.icon_filename)

    for tweet in tweets:
        tweet.good = TweetGoodUser.query.filter_by(tweet_id=tweet.id, user_id=current_user.id).first() is not None
    return render_template('tweets/index.html', tweets=tweets)

@app.route('/tweets/<int:id>/edit',methods=['GET','POST'])
def update(id):
    tweet = Tweet.query.get(id)
    if request.method == 'GET':
        return render_template('edit.html',post=tweet)
    else:
        tweet.title = request.form.get('title')
        tweet.body = request.form.get('body')
        db.session.commit()
        return redirect('/')
    
@app.route('/tweets/<int:id>/delete',methods=['GET'])
@login_required
def delete(id):
    tweet = Tweet.query.get_or_404(id)
    #投稿を削除
    db.session.delete(tweet)
    #削除を反映
    db.session.commit()
    return redirect('/tweets')

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
         if user and check_password_hash(user.password, password):
             login_user(user)
             return redirect('/tweets')
         else:
             return "ユーザー名またはパスワードが間違っています"
     else:
         return render_template('login.html')
     
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('login')

@app.route("/good", methods=["POST"])
@login_required
def good():
    tweet_id = request.json['tweet_id']  # post_id じゃなく tweet_id
    tweet = Tweet.query.get(tweet_id)
    if not tweet:
        return jsonify({'error': 'Tweet not found'}), 404

    good_record = TweetGoodUser.query.filter_by(tweet_id=tweet_id, user_id=current_user.id).first()

    if good_record:
        db.session.delete(good_record)
        tweet.good_count -= 1
    else:
        new_good = TweetGoodUser(tweet_id=tweet_id, user_id=current_user.id)
        db.session.add(new_good)
        tweet.good_count += 1

    db.session.commit()
    return jsonify({'good_count': tweet.good_count})

@app.route('/add_tweet')
def add_tweet():
    tweet = Tweet(title='恋愛相談', body='気になる人がいます')
    db.session.add(tweet)
    db.session.commit()
    return '追加しました'

@app.route('/tweets/<int:tweet_id>/comment', methods=['POST'])
@login_required
def post_comment(tweet_id):
    body = request.form.get('comment')
    if body:
        comment = Comment(body=body, tweet_id=tweet_id, user_id=current_user.id)
        db.session.add(comment)
        db.session.commit()
    return redirect(f'/tweets/{tweet_id}')

@app.route('/tweets/<int:tweet_id>')
@login_required
def tweet_detail(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    tweet.good = TweetGoodUser.query.filter_by(tweet_id=tweet.id, user_id=current_user.id).first() is not None
    return render_template('tweets/detail.html', tweet=tweet)

@app.route('/users/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    tweets = Tweet.query.filter_by(user_id=user.id).order_by(
        Tweet.id.desc()).all()
    return render_template('user.html', user=user, tweets=tweets)


@app.route("/test_template")
def test_template():
    return render_template("edit_profile.html",user=current_user)

@app.route("/about")
def about():
    return render_template("about.html")

# app.py
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'static/user_icons'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # プロフィール画像のアップロード処理
        file = request.files.get('icon')
        if file and allowed_file(file.filename): 
           cleaned_filename = secure_filename(f"{current_user.id}_{file.filename.strip()}")
           file.save(os.path.join(app.config['UPLOAD_FOLDER'], cleaned_filename))
           current_user.icon_filename = cleaned_filename

        # その他のプロフィール情報も更新
        current_user.hobby = request.form.get('hobby')
        current_user.mbti = request.form.get('mbti')
        current_user.message = request.form.get('message')

        db.session.commit()
        return redirect(url_for('user_profile', username=current_user.username))

    return render_template('edit_profile.html', user=current_user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
