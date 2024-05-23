import sqlalchemy as sa
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from omeg.conf.boost import db
from omeg.data.load import cpf_strfmt, date_strfmt, payload
from omeg.mold.models import Enrollment, Professor, School, Student
from omeg.user.forms import student_registration_form

bp_user_routes = Blueprint(
    "bp_user_routes",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@bp_user_routes.route("/professor/<taxnr>")
@login_required
def professor_dashboard(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        return render_template(
            "professor_dashboard.html",
            payload=payload,
            professor=professor,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/dates")
def dates(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        return render_template(
            "dates.html",
            payload=payload,
            professor=professor,
            taxnr=taxnr,
        )


@bp_user_routes.route("/professor/<taxnr>/inep")
@login_required
def inep(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        schools = db.session.scalars(
            sa.select(School).order_by(School.city)
        ).all()
        return render_template(
            "schools.html",
            payload=payload,
            professor=professor,
            schools=schools,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/students")
@login_required
def registered_students(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        students = (
            db.session.query(
                Student.cpfnr,
                Student.fname,
                Student.birth,
                Student.email,
                Enrollment.inep,
                Enrollment.roll,
            )
            .where(
                Enrollment.taxnr == taxnr,
                Enrollment.cpfnr == Student.cpfnr,
                Enrollment.year == payload["edition"],
            )
            .order_by(
                Enrollment.roll,
                Student.fname,
            ).all()
        )
        return render_template(
            "registered_students.html",
            payload=payload,
            professor=professor,
            taxnr=taxnr,
            students=students,
        )


@bp_user_routes.route(
    "/professor/<taxnr>/new_student", methods=["GET", "POST"]
)
@login_required
def student_registration(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        form = student_registration_form()
        if form.validate_on_submit():
            student = Student(
                cpfnr=cpf_strfmt(form.cpfnr.data),
                fname=form.fname.data,
                birth=date_strfmt(form.birth.data),
                email=form.email.data,
            )
            enrollment = Enrollment(
                cpfnr=cpf_strfmt(form.cpfnr.data),
                taxnr=taxnr,
                inep=form.inep.data,
                year=payload["edition"],
                roll=form.roll.data,
                gift="N",
            )
            db.session.add(student)
            db.session.commit()
            db.session.add(enrollment)
            db.session.commit()
            flash("Estudante cadastrado com sucesso!")
            return redirect(
                url_for("bp_user_routes.professor_dashboard", taxnr=taxnr)
            )
    return render_template(
        "student_registration.html",
        payload=payload,
        professor=professor,
        taxnr=taxnr,
        form=form,
    )


@bp_user_routes.route("/professor/<taxnr>/extract")
@login_required
def students_extract(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        extract1 = {
            inep[0]: {
                i: db.session.query(Enrollment)
                .where(
                    Enrollment.inep == inep[0],
                    Enrollment.taxnr == taxnr,
                    Enrollment.year == payload["edition"],
                    Enrollment.roll == i,
                )
                .count()
                for i in [1, 2, 3]
            }
            for inep in db.session.query(Enrollment.inep)
            .where(
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
            )
            .all()
        }
        extract2 = {
            inep: sum(extract1[inep].values()) for inep in extract1.keys()
        }
        extract3 = {
            i: sum(extract1[inep][i] for inep in extract1.keys())
            for i in [1, 2, 3]
        }
        extract4 = sum(v for v in extract3.values())
        extract5 = {
            inep: db.session.query(School.name)
            .where(School.inep == inep)
            .one()[0]
            for inep in extract1.keys()
        }
        return render_template(
            "students_extract.html",
            payload=payload,
            professor=professor,
            extract1=extract1,
            extract2=extract2,
            extract3=extract3,
            extract4=extract4,
            extract5=extract5,
        )
