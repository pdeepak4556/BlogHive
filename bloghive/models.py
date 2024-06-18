from sqlalchemy import BLOB

from bloghive import db, login_manager
from flask import current_app
from datetime import datetime
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )

likes = db.Table('likes',
                 db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                 db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                 db.Column('liked', db.Boolean, nullable=False, default=False),
                 )

dislikes = db.Table('dislikes',
                    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                    db.Column('disliked', db.Boolean, nullable=False, default=False),
                    )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(BLOB)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    about = db.Column(db.String(500), nullable=True)
    draft_title = db.Column(db.String(100), nullable=True)
    draft_content = db.Column(db.Text, nullable=True)

    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    like = db.Relationship('Post', secondary=likes, backref='likes')
    dislike = db.Relationship('Post', secondary=dislikes, backref='dislikes')
    comments = db.Relationship('Comment', backref='user', cascade='all, delete-orphan')

    def get_reset_token(self, expires_seconds=300):
        s = Serializer(current_app.config['SECRET_KEY'], expires_seconds)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
            return User.query.get(user_id)
        except:
            return None

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        return Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id).order_by(
            Post.date_posted.desc())

    def check_like(self, post):
        if post in self.like:
            return True

    def check_dislike(self, post):
        if post in self.dislike:
            return True

    def like_post(self, post):
        if self.check_like(post):
            self.like.remove(post)
        else:
            self.like.append(post)
        if self.check_dislike(post):
            self.dislike.remove(post)

    def dislike_post(self, post):
        if self.check_dislike(post):
            self.dislike.remove(post)
        else:
            self.dislike.append(post)
        if self.check_like(post):
            self.like.remove(post)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now().astimezone())
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.now().astimezone())
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    views = db.Column(db.Integer)
    comments = db.Relationship('Comment', backref='post', cascade='all, delete-orphan')

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now().astimezone())
    content = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
