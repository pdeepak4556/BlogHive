import base64
import os

from flask import Blueprint, redirect, url_for, request, flash, render_template
from flask_login import current_user, login_user, logout_user, login_required

from bloghive import bcrypt, db
from bloghive.models import User, Post
from bloghive.users.forms import LoginForm, RegistrationForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm, \
    ProfilePhotoForm
from bloghive.users.utils import send_reset_email

users = Blueprint('users', __name__)


@users.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Check email or password!')
    return render_template('login.html', title='Sign in', form=form)


@users.route("/register", methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        path = os.path.join(os.getcwd(), 'bloghive', 'static', 'profile_pics', 'default.png')
        with open(path, 'rb') as file:
            img_data = file.read()

        user = User(username=form.username.data, email=form.email.data, password=hashed_password, image_file=img_data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('users.login'))
    return render_template('register.html', title="Register", form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route("/account", methods=['POST', 'GET'])
@login_required
def account():
    form = UpdateAccountForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.about = form.about.data
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.about.data = current_user.about
    return render_template('account.html', title="Account", form=form)


@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    image_file = base64.b64encode(user.image_file).decode('utf-8')
    form = ProfilePhotoForm()
    # Check if a user is logged in
    if current_user.is_authenticated:
        return render_template("user_post.html", posts=posts, user=user, form=form, logged_in=True,
                               image_file=image_file)
    else:
        return render_template("user_post.html", posts=posts, user=user, form=form, logged_out=True,
                               image_file=image_file)


@users.route("/reset-password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Email sent', "reset-email")
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', form=form, title="Reset Request")


@users.route("/reset-password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Token invalid or Expired')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        return redirect(url_for('users.login'))
    return render_template('reset_password.html', form=form, title="Reset Password")


@users.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return redirect(url_for('main.home'))
    if user == current_user:
        return redirect(url_for('users.user_posts', username=username))
    current_user.follow(user)
    db.session.commit()
    return redirect(url_for('users.user_posts', username=username))


@users.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return redirect(url_for('main.home'))
    if user == current_user:
        return redirect(url_for('main.home', username=username))
    current_user.unfollow(user)
    db.session.commit()
    return redirect(url_for('users.user_posts', username=username))


from PIL import Image, ExifTags
from io import BytesIO


@users.route('/upload_pic', methods=['POST'])
@login_required
def upload_pic():
    picture = request.files['file']
    if picture.filename != '':
        output_size = (150, 150)
        i = Image.open(picture)

        # Check if image has orientation info
        if hasattr(i, '_getexif') and i._getexif():
            # Get orientation tag (key 274)
            exif = dict((ExifTags.TAGS.get(k, k), v) for k, v in i._getexif().items())
            orientation = exif.get('Orientation', 1)

            # Apply orientation correction
            if orientation == 3:
                i = i.transpose(Image.ROTATE_180)
            elif orientation == 6:
                i = i.transpose(Image.ROTATE_270)
            elif orientation == 8:
                i = i.transpose(Image.ROTATE_90)

        # Crop the top-left part of the image
        width, height = i.size
        left = 0
        top = 0
        right = min(width, height)
        bottom = min(width, height)

        i = i.crop((left, top, right, bottom))
        i = i.resize(output_size)

        # Convert to RGB mode
        i = i.convert("RGB")

        img_io = BytesIO()
        i.save(img_io, format='JPEG')
        img_data = img_io.getvalue()

        current_user.image_file = img_data
        db.session.commit()
    return redirect(url_for('users.user_posts', username=current_user.username))
