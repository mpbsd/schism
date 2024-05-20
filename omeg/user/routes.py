import sqlalchemy as sa
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from omeg.conf.boost import db
from omeg.data.load import cpf_strfmt, payload
from omeg.mold.models import Enrollment, Professor, School, Student
from omeg.user.forms import student_registration_form

bp_user_routes = Blueprint(
    "bp_user_routes",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@bp_user_routes.route("/professor/<cpfP>")
@login_required
def professor_dashboard(cpfP):
    if cpfP == current_user.cpfP:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.cpfP == cpfP)
        )
        return render_template(
            "professor_dashboard.html",
            payload=payload,
            professor=professor,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<cpfP>/inep")
@login_required
def inep(cpfP):
    if cpfP == current_user.cpfP:
        schools = db.session.scalars(
            sa.select(School).order_by(School.city)
        ).all()
        return render_template(
            "schools.html",
            payload=payload,
            schools=schools,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<cpfP>/extract")
@login_required
def students_extract(cpfP):
    if cpfP == current_user.cpfP:
        level_1 = db.session.query(Enrollment).where(
            Enrollment.cpfP == cpfP,
            Enrollment.year == payload["edition"],
            Enrollment.roll == 1,
        )
        level_2 = db.session.query(Enrollment).where(
            Enrollment.cpfP == cpfP,
            Enrollment.year == payload["edition"],
            Enrollment.roll == 2,
        )
        level_3 = db.session.query(Enrollment).where(
            Enrollment.cpfP == cpfP,
            Enrollment.year == payload["edition"],
            Enrollment.roll == 3,
        )
        return render_template(
            "students_extract.html",
            payload=payload,
            Q1=level_1.count(),
            Q2=level_2.count(),
            Q3=level_3.count(),
        )


@bp_user_routes.route("/professor/<cpfP>/students")
@login_required
def registered_students(cpfP):
    if cpfP == current_user.cpfP:
        students = (
            db.session.query(
                Student.cpfS,
                Student.name,
                Student.bday,
                Student.mail,
                Enrollment.inep,
                Enrollment.roll,
            )
            .where(
                Enrollment.cpfS == Student.cpfS,
                Enrollment.cpfP == cpfP,
                Enrollment.year == payload["edition"],
            )
            .order_by(
                Enrollment.roll,
                Student.name,
            )
        )
        return render_template(
            "registered_students.html",
            payload=payload,
            cpfP=cpfP,
            students=students,
        )


@bp_user_routes.route("/professor/<cpfP>/new_student", methods=["GET", "POST"])
@login_required
def student_registration(cpfP):
    if cpfP == current_user.cpfP:
        form = student_registration_form()
        if form.validate_on_submit():
            student = Student(
                cpfS=cpf_strfmt(form.cpfS.data),
                name=form.name.data,
                bday=form.bday.data,
                mail=form.mail.data,
            )
            enrollment = Enrollment(
                cpfS=cpf_strfmt(form.cpfS.data),
                cpfP=cpfP,
                inep=form.inep.data,
                year=payload["edition"],
                roll=form.roll.data,
                gift="None",
            )
            db.session.add(student)
            db.session.add(enrollment)
            db.session.commit()
            flash("Estudante cadastrado com sucesso!")
            return redirect(
                url_for("bp_user_routes.professor_dashboard", cpfP=cpfP)
            )
    return render_template(
        "student_registration.html", payload=payload, cpfP=cpfP, form=form
    )
