import os

from bloghive import create_app, db, time_ago

app = create_app()
config = app.config

secret_key = config['SECRET_KEY']
db_uri = config['SQLALCHEMY_DATABASE_URI']
email_user = config['EMAIL_USER']
email_pass = config['EMAIL_PASS']
mail_server = config['MAIL_SERVER']
mail_port = config['MAIL_PORT']
mail_use_tls = config['MAIL_USE_TLS']

with app.app_context():
    if not os.path.exists('instance/site.db'):
        db.create_all()

app.jinja_env.globals.update(time_ago=time_ago)

if __name__ == '__main__':
    app.run(debug=True)
