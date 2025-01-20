from flask import Flask, render_template, request, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"<user {self.id}>"


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<post {self.id}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_user():
    return dict(user=current_user, posts=Post.query.all())


@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts, user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'))

        if username and email and password:
            if User.query.filter_by(email=email).first():
                flash('Email already taken. Try another one.', 'danger')
            if User.query.filter_by(username=username).first():
                flash('Username already taken. Try another one.', 'danger')
            else:
                try:
                    user = User(username=username, email=email, password=password)
                    db.session.add(user)
                    db.session.flush()
                    db.session.commit()
                    flash('User registered successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    print('Ошибка при добавлении юзера в бд:', e)

                return redirect(url_for('login'))
        else:
            flash('All fields are required!', 'danger')

    return render_template('register.html')


@app.route('/<int:post_id>')
def post(post_id):
    '''Получить из бд пост по айди'''
    post = Post.query.get(post_id)
    return render_template('post.html', post=post, user=current_user)


@app.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        # здесь должна быть проверка введенных данных
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            try:
                post = Post(title=title, content=content, author_id=current_user.id)
                db.session.add(post)
                db.session.flush()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print('Ошибка добавления в бд')
                print(e)

            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email and password:
            user = User.query.filter(User.email == email).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash("You've logged in successfully!", 'success')
                return render_template('index.html', posts=Post.query.all(), user=current_user)
            else:
                flash('Wrong email or password', 'danger')
        else:
            flash('All fields required', 'danger')

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect('/')


@app.route('/posts/user_<int:user_id>')
@login_required
def users_posts(user_id):
    posts = Post.query.filter_by(author_id=user_id).all()
    return render_template('posts.html', posts=posts)


@app.route('/posts/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        post.title = title
        post.content = content

        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))

    return render_template('edit.html', post=post)


@app.route('/posts/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted.', 'danger')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)