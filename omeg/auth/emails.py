from flask import current_app, render_template

from omeg.conf.boost import send_email
from omeg.mold.models import Professor


def send_registration_request_email(mail):
    token = Professor.get_registration_request_token(mail)
    send_email(
        "[OMEG] Cadastro de Professor",
        sender=current_app.config["ADMINS"][0],
        recipients=[mail],
        text_body=render_template(
            "registration_request_mail.txt", token=token
        ),
        html_body=render_template(
            "registration_request_mail.html", token=token
        ),
    )


def send_password_reset_email(professor):
    token = professor.get_reset_password_token()
    send_email(
        "[OMEG] Redefinição de senha",
        sender=current_app.config["ADMINS"][0],
        recipients=[professor.mail],
        text_body=render_template(
            "request_password_reset_msg.txt",
            professor=professor,
            token=token,
        ),
        html_body=render_template(
            "request_password_reset_msg.html",
            professor=professor,
            token=token,
        ),
    )
