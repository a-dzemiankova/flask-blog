from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from .models import Post, User
from . import db


def init_routes(app):

    @app.context_processor
    def inject_user():
        return dict(user=current_user, posts=Post.query.all())

    @app.route('/')
    @app.route('/posts')
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

    @app.route('/user/posts')
    @login_required
    def users_posts():
        posts = Post.query.filter_by(author_id=current_user.id).all()
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