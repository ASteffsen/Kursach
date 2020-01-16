import os
import secrets
from flask import render_template, url_for, flash, redirect, request
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, HistoryForm, PostForm, CharacterForm
from app.models import User, Post, History, Character
from flask_login import login_user, current_user, logout_user, login_required



@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    form_picture.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.about = form.about.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

@app.route("/history_new", methods=['GET', 'POST'])
@login_required
def new_history():
    form = HistoryForm()
    if form.validate_on_submit():
        history = History(title=form.title.data, info=form.info.data, author=current_user)
        db.session.add(history)
        db.session.commit()
        flash('Your story has been created!', 'success')
        return redirect(url_for('history', history_id = history.id))

    return render_template('create_history.html', title='New History', form=form)

@app.route("/history/<int:history_id>/character_new", methods=['GET', 'POST'])
@login_required
def new_character(history_id):
    form = CharacterForm()
    if form.validate_on_submit():
        story = History.query.filter_by(id=history_id).first()
        character = Character(name=form.name.data, info=form.info.data, author=current_user, story=story)
        db.session.add(character)
        db.session.commit()
        flash('Your character has been created!', 'success')
        return redirect(url_for('character', history_id = history_id, character_id = character.id))

    return render_template('create_character.html', title='New History', form=form)

@app.route("/history/<int:history_id>/character/<int:character_id>/post_new", methods=['GET', 'POST'])
@login_required
def new_post(history_id, character_id):
    form = PostForm()
    if form.validate_on_submit():
        story = History.query.filter_by(id=history_id).first()
        char = Character.query.filter_by(id=character_id).first()
        post = Post(title=form.title.data, content=form.content.data, author=current_user, story=story, char=char)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))

    return render_template('create_post.html', title='New History', form=form)

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/user/<int:user_id>")
def user(user_id):
    histories = History.query.filter_by(user_id=user_id)
    user = User.query.get_or_404(user_id)
    return render_template('user.html', user=user, histories=histories )

@app.route("/history/<int:history_id>")
def history(history_id):
    characters = Character.query.filter_by(history_id=history_id)
    history = History.query.get_or_404(history_id)
    return render_template('history.html', history=history, characters=characters )

@app.route("/history/<int:history_id>/character/<int:character_id>")
def character(history_id, character_id):
    posts = Post.query.filter_by(character_id=character_id)
    character = Character.query.get_or_404(character_id)
    return render_template('character.html', character=character, posts=posts)

