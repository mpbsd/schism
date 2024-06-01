import re

import sqlalchemy as sa
from flask import Blueprint, redirect, render_template, url_for
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

bp_auth_routes = Blueprint("bp_auth_routes", __name__)


@bp_auth_routes.route(
    "/professor/registration/request", methods=["GET", "POST"]
)
def request_registration():
    if current_user.is_authenticated:
        return redirect(
            url_for(
                "bp_user_routes.professor_dashboard",
                taxnr=current_user.taxnr,
            )
        )
    form = professor_registration_request_form()
    if form.validate_on_submit():
        professor = db.session.scalar(
            sa.select(Professor).where(
                Professor.email == cpf_strfmt(form.email.data)
            )
        )
        if not professor:
            send_registration_request_email(form.email.data)
        return redirect(url_for("bp_home_routes.home"))
    return render_template(
        "auth/registration/request/page.html",
        edition=payload["edition"],
        form=form,
    )


@bp_auth_routes.route(
    "/professor/registration/<token>", methods=["GET", "POST"]
)
def registration(token):
    if current_user.is_authenticated:
        return redirect(
            url_for(
                "bp_user_routes.professor_dashboard",
                taxnr=current_user.taxnr,
            )
        )
    email = Professor.verify_registration_request_token(token)
    form = professor_registration_form(email=email)
    if form.validate_on_submit():
        professor = Professor(
            taxnr=cpf_strfmt(form.taxnr.data),
            fname=re.sub(r"\s+", r" ", form.fname.data),
            email=form.email.data,
        )
        professor.set_password(form.password1.data)
        db.session.add(professor)
        db.session.commit()
        return redirect(url_for("bp_auth_routes.login"))
    return render_template(
        "auth/registration/professor.html",
        edition=payload["edition"],
        token=token,
        form=form,
    )


@bp_auth_routes.route(
    "/professor/password/request/reset", methods=["GET", "POST"]
)
def request_password_reset():
    if current_user.is_authenticated:
        return redirect(
            url_for(
                "bp_user_routes.professor_dashboard", taxnr=current_user.taxnr
            )
        )
    form = reset_password_request_form()
    if form.validate_on_submit():
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.email == form.email.data)
        )
        if professor:
            send_password_reset_email(professor)
        return redirect(url_for("bp_home_routes.home"))
    return render_template(
        "auth/password/request/page.html",
        edition=payload["edition"],
        title="Redefinir Senha",
        form=form,
    )


@bp_auth_routes.route(
    "/professor/password/reset/<token>", methods=["GET", "POST"]
)
def password_reset(token):
    if current_user.is_authenticated:
        return redirect(
            url_for(
                "bp_user_routes.professor_dashboard", taxnr=current_user.taxnr
            )
        )
    professor = Professor.verify_reset_password_token(token)
    if not professor:
        return redirect(url_for("bp_home_routes.home"))
    form = reset_password_form()
    if form.validate_on_submit():
        professor.set_password(form.password1.data)
        db.session.commit()
        return redirect(url_for("bp_auth_routes.login"))
    return render_template(
        "auth/password/reset.html",
        edition=payload["edition"],
        form=form,
    )


@bp_auth_routes.route("/professor/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(
            url_for(
                "bp_user_routes.professor_dashboard", taxnr=current_user.taxnr
            )
        )
    form = login_form()
    if form.validate_on_submit():
        professor = db.session.scalar(
            sa.select(Professor).where(
                Professor.taxnr == cpf_strfmt(form.taxnr.data)
            )
        )
        if professor is None:
            return redirect(url_for("bp_home_routes.home"))
        else:
            if professor.check_password(form.password.data) is False:
                return redirect(url_for("bp_auth_routes.login"))
            else:
                login_user(professor)
                return redirect(
                    url_for(
                        "bp_user_routes.professor_dashboard",
                        taxnr=current_user.taxnr,
                    )
                )
    return render_template(
        "auth/login.html",
        edition=payload["edition"],
        form=form,
    )


@bp_auth_routes.route("/professor/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("bp_home_routes.home"))
