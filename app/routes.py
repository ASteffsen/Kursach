import os
import secrets
from flask import render_template, url_for, flash, redirect, request, abort
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, HistoryForm, PostForm, CharacterForm
from app.models import User, Post, History, Character
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)


@app.route("/feed")
def feed():
    posts = current_user.followed_posts().all()
    return render_template('feed.html', posts=posts)


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
        flash('Аккаунт создан. Добро пожаловать', 'success')
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
            return redirect(next_page) if next_page else redirect(url_for('feed'))
        else:
            flash('Проверьте введенные данные', 'danger')
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
        flash('Информация обновлена', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about.data = current_user.about
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
        flash('Вы создали историю', 'success')
        return redirect(url_for('history', history_id=history.id))

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
        flash('Вы создали персонажа', 'success')
        return redirect(url_for('character', history_id=history_id, character_id=character.id))

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
        flash('Вы создали пост', 'success')
        return redirect(url_for('home'))

    return render_template('create_post.html', title='New History', form=form)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Информация в посте обновлена', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Пост удален', 'success')
    return redirect(url_for('character', history_id=post.history_id, character_id=post.character_id))


@app.route("/user/<int:user_id>")
def user(user_id):
    histories = History.query.filter_by(user_id=user_id)
    user = User.query.get_or_404(user_id)
    return render_template('user.html', user=user, histories=histories)


@app.route("/history/<int:history_id>")
def history(history_id):
    characters = Character.query.filter_by(history_id=history_id)
    history = History.query.get_or_404(history_id)
    return render_template('history.html', history=history, characters=characters)


@app.route("/history/<int:history_id>/update", methods=['GET', 'POST'])
@login_required
def update_history(history_id):
    history = History.query.get_or_404(history_id)
    if history.author != current_user:
        abort(403)
    form = HistoryForm()
    if form.validate_on_submit():
        history.title = form.title.data
        history.info = form.info.data
        db.session.commit()
        flash('Информация в истории обновлена', 'success')
        return redirect(url_for('history', history_id=history.id))
    elif request.method == 'GET':
        form.title.data = history.title
        form.info.data = history.info
    return render_template('create_history.html', title='Изменить историю',
                           form=form, legend='Update History')


@app.route("/history/<int:history_id>/delete", methods=['POST'])
@login_required
def delete_history(history_id):
    history = History.query.get_or_404(history_id)
    if history.author != current_user:
        abort(403)
    character = Character.query.filter_by(history_id=history_id).first()
    if character is not None:
        flash('Вы не можете удалить эту историю, так как в ней есть персонажи.')
        return redirect(url_for('history', history_id=history_id))
    db.session.delete(history)
    db.session.commit()
    flash('Пост удален', 'success')
    return redirect(url_for('home'))


@app.route("/history/<int:history_id>/character/<int:character_id>")
def character(history_id, character_id):
    posts = Post.query.filter_by(character_id=character_id)
    character = Character.query.get_or_404(character_id)
    return render_template('character.html', character=character, posts=posts)


@app.route("/history/<int:history_id>/character/<int:character_id>/update", methods=['GET', 'POST'])
@login_required
def update_character(history_id, character_id):
    character = Character.query.get_or_404(character_id)
    if character.author != current_user:
        abort(403)
    form = CharacterForm()
    if form.validate_on_submit():
        character.name = form.name.data
        character.info = form.info.data
        db.session.commit()
        flash('Информация о персонаже обновлена', 'success')
        return redirect(url_for('character', history_id=history_id, character_id=character_id))
    elif request.method == 'GET':
        form.name.data = character.name
        form.info.data = character.info
    return render_template('create_character.html', title='Изменить персонажа',
                           form=form, legend='Update History')


@app.route("/history/<int:history_id>/character/<int:character_id>/delete", methods=['POST'])
@login_required
def delete_character(history_id, character_id):
    character = Character.query.get_or_404(character_id)
    if character.author != current_user:
        abort(403)
    post = Post.query.filter_by(character_id=character_id).first()
    if post is not None:
        flash('Вы не можете удалить этого персонажа, так как про него есть посты.')
        return redirect(url_for('character', history_id=history_id, character_id=character_id))
    db.session.delete(character)
    db.session.commit()
    flash('Персонаж удален', 'success')
    return redirect(url_for('history', history_id=history_id))


@app.route('/user/<int:user_id>/follow')
@login_required
def follow(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        flash('Пользователь {} не найден.'.format(user.username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('Нарциссизм у нас не в почете')
        return redirect(url_for('user', user_id=user_id))
    current_user.follow(user)
    db.session.commit()
    flash('Вы подписались на {}!'.format(user.username))
    return redirect(url_for('user', user_id=user_id))


@app.route('/user/<int:user_id>/unfollow')
@login_required
def unfollow(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        flash('Пользователь {} не найден'.format(user.username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('У тебя не настолько плохие посты, ну')
        return redirect(url_for('user', user_id=user_id))
    current_user.unfollow(user)
    db.session.commit()
    flash('Вы отписались от {}.'.format(user.username))
    return redirect(url_for('user', user_id=user_id))

