from flask import Flask, render_template, request, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    posts = db.relationship('Post', backref='users', lazy=True)

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


@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)


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

                return redirect(url_for('index'))
        else:
            flash('All fields are required!', 'danger')

    return render_template('register.html')


@app.route('/<int:post_id>')
def post(post_id):
    '''Получить из бд пост по айди'''
    post = Post.query.get(post_id)
    return render_template('post.html', post=post)


@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        # здесь должна быть проверка введенных данных
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            try:
                post = Post(title=title, content=content, author_id=1)
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
                flash("You've logged in successfully!", 'success')
            else:
                flash('Wrong email or password', 'danger')
        else:
            flash('All fields required', 'danger')

    return render_template('login.html')


#
#
# @app.route('/<int:id>/edit', methods=('GET', 'POST'))
# def edit(id):
#     post = get_post(id)
#     if request.method == 'POST':
#         title = request.form['title']
#         content = request.form['content']
#
#         if not title:
#             flash('Title is required!')
#         else:
#             conn = get_db_connection()
#             conn.execute('UPDATE posts SET title = ?, content = ?'
#                          ' WHERE id = ?',
#                          (title, content, id))
#             conn.commit()
#             conn.close()
#             return redirect(url_for('index'))
#
#     return render_template('edit.html', post=post)
#
#
# @app.route('/<int:id>/delete', methods=('POST',))
# def delete(id):
#     post = get_post(id)
#     conn = get_db_connection()
#     conn.execute('DELETE FROM posts WHERE id = ?', (id,))
#     conn.commit()
#     conn.close()
#     flash('"{}" was successfully deleted!'.format(post['title']))
#     return redirect(url_for('index'))
#
#
if __name__ == '__main__':
    app.run(debug=True)