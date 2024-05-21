import sqlalchemy as sa
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from omeg.auth.emails import (
    send_password_reset_email,
    send_registration_request_email,
)
from omeg.auth.forms import (
    login_form,
    professor_registration_form,
    professor_registration_request_form,
    reset_password_form,
    reset_password_request_form,
)
from omeg.conf.boost import db
from omeg.data.load import cpf_strfmt, payload
from omeg.mold.models import Professor

bp_auth_routes = Blueprint(
    "bp_auth_routes",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@bp_auth_routes.route("/registration-request", methods=["GET", "POST"])
def request_registration():
    if current_user.is_authenticated:
        return redirect(url_for("bp_home_routes.home"))
    form = professor_registration_request_form()
    if form.validate_on_submit():
        flash("Por favor, cheque sua caixa de entrada.")
        professor = db.session.scalar(
            sa.select(Professor).where(
                Professor.mail == cpf_strfmt(form.mail.data)
            )
        )
        if not professor:
            send_registration_request_email(form.mail.data)
        return redirect(url_for("bp_home_routes.home"))
    return render_template(
        "registration_request_page.html", payload=payload, form=form
    )


@bp_auth_routes.route("/registration/<token>", methods=["GET", "POST"])
def registration(token):
    if current_user.is_authenticated:
        return redirect(url_for("bp_home_routes.home"))
    mail = Professor.verify_registration_request_token(token)
    form = professor_registration_form(mail=mail)
    if form.validate_on_submit():
        professor = Professor(
            cpfP=cpf_strfmt(form.cpfP.data),
            name=form.name.data,
            mail=form.mail.data,
        )
        professor.set_password(form.password1.data)
        db.session.add(professor)
        db.session.commit()
        flash("Usuário cadastrado com sucesso.")
        return redirect(url_for("bp_auth_routes.login", payload=payload))
    return render_template(
        "registration.html", payload=payload, form=form, token=token
    )


@bp_auth_routes.route("/request_password_reset", methods=["GET", "POST"])
def request_password_reset():
    if current_user.is_authenticated:
        return redirect(
            url_for(
                "bp_user_routes.professor_dashboard",
                cpfP=current_user.cpfP
            )
        )
    form = reset_password_request_form()
    if form.validate_on_submit():
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.mail == form.mail.data)
        )
        flash("Cheque a sua caixa de e-mails.")
        if professor:
            send_password_reset_email(professor)
        return redirect(url_for("bp_auth_routes.login"))
    return render_template(
        "password_reset_request_page.html",
        payload=payload,
        title="Redefinir Senha",
        form=form,
    )


@bp_auth_routes.route("/password_reset/<token>", methods=["GET", "POST"])
def password_reset(token):
    if current_user.is_authenticated:
        return redirect(
            url_for(
                "bp_user_routes.professor_dashboard",
                cpfP=current_user.cpfP
            )
        )
    professor = Professor.verify_reset_password_token(token)
    if not professor:
        return redirect(url_for("bp_home_routes.home"))
    form = reset_password_form()
    if form.validate_on_submit():
        professor.set_password(form.password.data)
        db.session.commit()
        flash("Senha redefinida com sucesso.")
        return redirect(url_for("bp_auth_routes.login"))
    return render_template("password_reset.html", payload=payload, form=form)


@bp_auth_routes.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(
            url_for(
                "bp_user_routes.professor_dashboard", cpfP=current_user.cpfP
            )
        )
    form = login_form()
    if form.validate_on_submit():
        professor = db.session.scalar(
            sa.select(Professor).where(
                Professor.cpfP == cpf_strfmt(form.cpfP.data)
            )
        )
        if professor is None:
            flash("CPF não encontrado")
            return redirect(url_for("bp_home_routes.home"))
        else:
            if professor.check_password(form.password.data) is False:
                flash("Senha incorreta")
                return redirect(url_for("bp_auth_routes.login"))
            else:
                login_user(professor)
                return redirect(
                    url_for(
                        "bp_user_routes.professor_dashboard",
                        cpfP=professor.cpfP,
                    )
                )
    return render_template("login.html", payload=payload, form=form)


@bp_auth_routes.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("bp_home_routes.home"))
