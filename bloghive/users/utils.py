from flask import url_for
from flask_mail import Message

from bloghive import mail


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='blogspot4556@gmail.com', recipients=[user.email])

    msg.body = f'''To reset your password visit the following link: {url_for('users.reset_password', token=token, _external=True)}

This link expires in 5 minutes!

If you did not make this request please ignore this mail.
'''
    mail.send(msg)
