import re

import sqlalchemy as sa
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from unidecode import unidecode

from omeg.conf.boost import db
from omeg.data.load import cpf_strfmt, date_strfmt, payload
from omeg.mold.models import Enrollment, Professor, School, Student
from omeg.user.forms import (
    edit_student_registration_form,
    student_registration_form,
)

bp_user_routes = Blueprint("bp_user_routes", __name__)


@bp_user_routes.route("/professor/<taxnr>")
@login_required
def professor_dashboard(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        return render_template(
            "user/professor_dashboard.html",
            payload=payload,
            professor=professor,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/dates")
def save_the_date(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        return render_template(
            "user/save_the_date.html",
            payload=payload,
            professor=professor,
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
            "user/schools.html",
            payload=payload,
            professor=professor,
            schools=schools,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


def students_extract_query(taxnr):
    # extract1 = {
    #   {
    #     inep: {
    #       1: qty_of_students_at_level_1,
    #       2: qty_of_students_at_level_2,
    #       3: qty_of_students_at_level_3
    #     }
    #     for each of the professor's schools
    #   }
    # }
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
    # extract2 = {
    #   inep: qty_of_students_in_total,
    #   for each of the professor's schools
    # }
    extract2 = {inep: sum(extract1[inep].values()) for inep in extract1.keys()}
    # extract3 = {
    #   i: qty_of_students_at_level_i_from_all_of_the_professors_schools,
    #   for i in [1, 2, 3]
    # }
    extract3 = {
        i: sum(extract1[inep][i] for inep in extract1.keys())
        for i in [1, 2, 3]
    }
    # extract4 = qty_of_students_in_total
    extract4 = sum(v for v in extract3.values())
    # extract5 = {
    #   inep: school_name,
    #   for each of the professor's schools
    # }
    extract5 = {
        inep: db.session.query(School.name).where(School.inep == inep).one()[0]
        for inep in extract1.keys()
    }
    extract = {
        1: extract1,
        2: extract2,
        3: extract3,
        4: extract4,
        5: extract5,
    }
    return extract


@bp_user_routes.route(
    "/professor/<taxnr>/student_registration", methods=["GET", "POST"]
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
                fname=re.sub(r"\s+", r" ", form.fname.data),
                birth=date_strfmt(form.birth.data, "yyyymmdd"),
                email=form.email.data,
            )
            enrollment = Enrollment(
                cpfnr=cpf_strfmt(form.cpfnr.data),
                taxnr=taxnr,
                inep=form.inep.data,
                year=payload["edition"],
                roll=form.roll.data,
                need=unidecode(form.need.data.lower()),
                gift="N",
            )
            quota = (
                db.session.query(Enrollment)
                .where(
                    Enrollment.taxnr == enrollment.taxnr,
                    Enrollment.inep == enrollment.inep,
                    Enrollment.roll == enrollment.roll,
                )
                .count()
            )
            if quota <= payload["quota"] - 1:
                enrollment_already_exists = (
                    db.session.query(Enrollment)
                    .where(
                        Enrollment.cpfnr == enrollment.cpfnr,
                        Enrollment.taxnr == enrollment.taxnr,
                        Enrollment.inep == enrollment.inep,
                        Enrollment.year == payload["edition"],
                    )
                    .all()
                )
                if not enrollment_already_exists:
                    db.session.add(student)
                    db.session.commit()
                    db.session.add(enrollment)
                    db.session.commit()
                    flash("Estudante cadastrado com sucesso!")
                return redirect(
                    url_for(
                        "bp_user_routes.registered_students",
                        payload=payload,
                        professor=professor,
                    )
                )
            else:
                extract = students_extract_query(professor.taxnr)
                flash("Quota atingida.")
                return render_template(
                    "user/quota_overflow.html",
                    payload=payload,
                    professor=professor,
                    roll=enrollment.roll,
                    extract=extract,
                )
    return render_template(
        "user/student_registration.html",
        payload=payload,
        professor=professor,
        form=form,
    )


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
            )
            .where(
                Enrollment.cpfnr == Student.cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
            )
            .order_by(
                Student.fname,
            )
            .all()
        )
        return render_template(
            "user/registered_students.html",
            payload=payload,
            professor=professor,
            students=students,
            date_strfmt=date_strfmt,
        )


@bp_user_routes.route("/professor/<taxnr>/enrollments_extract")
@login_required
def enrollments_extract(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        enrollments = (
            db.session.query(
                Student.fname,
                Student.cpfnr,
                Enrollment.roll,
                Enrollment.need,
                School.name,
                School.inep,
            )
            .where(
                Enrollment.taxnr == taxnr,
                Student.cpfnr == Enrollment.cpfnr,
                School.inep == Enrollment.inep,
                Enrollment.year == payload["edition"],
            )
            .order_by(Enrollment.roll)
            .all()
        )
        return render_template(
            "user/enrollments_extract.html",
            payload=payload,
            professor=professor,
            enrollments=enrollments,
        )


@bp_user_routes.route("/professor/<taxnr>/numeric_extract")
@login_required
def numeric_extract(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        extract = students_extract_query(professor.taxnr)
        return render_template(
            "user/numeric_extract.html",
            payload=payload,
            professor=professor,
            extract=extract,
        )


@bp_user_routes.route(
    "/professor/<taxnr>/request_student_registration_edition"
)
@login_required
def request_student_registration_edition(taxnr):
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
            )
            .where(
                Enrollment.cpfnr == Student.cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
            )
            .order_by(
                Student.fname,
            )
            .all()
        )
        return render_template(
            "user/registration/request.html",
            payload=payload,
            professor=professor,
            students=students,
            date_strfmt=date_strfmt,
        )


# @bp_user_routes.route(
#     "/professor/<taxnr>/edit/<cpfnr>",
#     methods=["GET", "POST"],
# )
# @login_required
# def edit_student_registration(taxnr, cpfnr):
#     if taxnr == current_user.taxnr:
#         professor = db.first_or_404(
#             sa.select(Professor).where(Professor.taxnr == taxnr)
#         )
#         student = db.session.query(Student).where(Student.cpfnr == cpfnr).one()
#         form = edit_student_registration_form(
#             cpfnr=student.cpfnr,
#             fname=student.fname,
#             birth=student.birth,
#             email=student.email,
#         )
#         if form.validate_on_submit():
#             student.verified = True
#             db.session.commit()
#             flash("Cadastro atualizado com sucesso!")
#             return redirect(
#                 url_for(
#                     "bp_user_routes.registered_students",
#                     payload=payload,
#                     professor=professor,
#                 )
#             )
#     return render_template(
#         "user/registration/edit/cpfnr.html",
#         payload=payload,
#         professor=professor,
#         student=student,
#         form=form,
#     )
