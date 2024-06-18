from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from bloghive.config import Config
from datetime import datetime, timezone

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
mail = Mail()
migrate = Migrate()


def time_ago(given_time):
    current_time = datetime.now(timezone.utc).timestamp()
    given_time = given_time.timestamp()

    difference = current_time - given_time

    if difference < 60:
        return "Just now"

    elif difference < 3600:
        minutes = int(difference / 60)
        if minutes == 1:
            return f"{minutes} min ago"
        return f"{minutes} mins ago"

    elif difference < 86400:
        hours = int(difference / 3600)
        if hours == 1:
            return f"{hours} hr ago"
        return f"{hours} hrs ago"

    elif difference < 604800:
        days = int(difference / 86400)
        if days == 1:
            return f"{days} day ago"
        return f"{days} days ago"

    elif difference < 2592000:
        weeks = int(difference / 604800)
        if weeks == 1:
            return f"{weeks} week ago"
        return f"{weeks} weeks ago"

    elif difference < 31536000:
        months = int(difference / 2592000)
        if months == 1:
            return f"{months} month ago"
        return f"{months} months ago"

    else:
        years = int(difference / 31536000)
        if years == 1:
            return f"{years} year ago"
        return f"{years} years ago"


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    from bloghive.users.routes import users
    from bloghive.posts.routes import posts
    from bloghive.main.routes import main
    from bloghive.errors.handlers import errors
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app
