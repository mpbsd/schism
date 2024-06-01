import re

import sqlalchemy as sa
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from unidecode import unidecode

from omeg.conf.boost import db
from omeg.data.load import cpf_strfmt, date_strfmt, payload
from omeg.mold.models import Enrollment, Professor, School, Student
from omeg.user.forms import (
    edit_enrollment_inep_form,
    edit_enrollment_need_form,
    edit_enrollment_roll_form,
    edit_student_birth_form,
    edit_student_cpfnr_form,
    edit_student_email_form,
    edit_student_fname_form,
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
            "user/dashboard.html",
            save_the_date=payload["save_the_date"],
            days_until=payload["days_until"],
            pfname=professor.fname,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/dates")
@login_required
def save_the_date(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        return render_template(
            "user/utils/save_the_date.html",
            pfname=professor.fname,
            save_the_date=payload["save_the_date"],
            days_until=payload["days_until"],
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


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
            "user/utils/inep.html",
            payload=payload,
            pfname=professor.fname,
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
    "/professor/<taxnr>/student/registration", methods=["GET", "POST"]
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
                need=re.sub(r"\s+", r" ", unidecode(form.need.data.lower())),
                gift="N",
            )
            quota = (
                db.session.query(Enrollment)
                .where(
                    Enrollment.inep == enrollment.inep,
                    Enrollment.year == payload["edition"],
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
                        pfname=professor.fname,
                        taxnr=taxnr,
                    )
                )
            else:
                extract = students_extract_query(professor.taxnr)
                flash("Quota atingida.")
                return render_template(
                    "user/registration/read/quota_overflow.html",
                    edition=payload["edition"],
                    quota=payload["quota"],
                    pfname=professor.fname,
                    roll=enrollment.roll,
                    extract=extract,
                )
        return render_template(
            "user/registration/create/student.html",
            edition=payload["edition"],
            pfname=professor.fname,
            form=form,
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
            )
            .where(
                Enrollment.cpfnr == Student.cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
            )
            .order_by(Student.fname)
            .all()
        )
        return render_template(
            "user/registration/read/registered_students.html",
            edition=payload["edition"],
            pfname=professor.fname,
            students=students,
            date_strfmt=date_strfmt,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


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
            "user/enrollment/read/enrollments_extract.html",
            edition=payload["edition"],
            pfname=professor.fname,
            enrollments=enrollments,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/numeric_extract")
@login_required
def numeric_extract(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        extract = students_extract_query(professor.taxnr)
        return render_template(
            "user/enrollment/read/numeric_extract.html",
            edition=payload["edition"],
            pfname=professor.fname,
            extract=extract,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/student/registration/update/request")
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
            .order_by(Student.fname)
            .all()
        )
        return render_template(
            "user/registration/update/request.html",
            edition=payload["edition"],
            pfname=professor.fname,
            students=students,
            date_strfmt=date_strfmt,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/students/update/<cpfnr>",
    methods=["GET", "POST"],
)
@login_required
def edit_student_registration(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        student = db.first_or_404(
            sa.select(Student).where(Student.cpfnr == cpfnr)
        )
        return render_template(
            "user/registration/update/student.html",
            edition=payload["edition"],
            pfname=professor.fname,
            student=student,
            date_strfmt=date_strfmt,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/students/update/<cpfnr>/cpfnr", methods=["GET", "POST"]
)
@login_required
def edit_student_cpfnr(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        student = db.first_or_404(
            sa.select(Student).where(Student.cpfnr == cpfnr)
        )
        form = edit_student_cpfnr_form(cpfnr=student.cpfnr)
        if form.validate_on_submit():
            student.cpfnr = cpf_strfmt(form.cpfnr.data)
            db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_registration",
                    taxnr=taxnr,
                    cpfnr=student.cpfnr,
                )
            )
        return render_template(
            "user/registration/update/field/cpfnr.html",
            edition=payload["edition"],
            pfname=professor.fname,
            student=student,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/students/update/<cpfnr>/fname", methods=["GET", "POST"]
)
@login_required
def edit_student_fname(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        student = db.first_or_404(
            sa.select(Student).where(Student.cpfnr == cpfnr)
        )
        form = edit_student_fname_form(fname=student.fname)
        if form.validate_on_submit():
            student.fname = re.sub(r"\s+", r" ", form.fname.data)
            db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_registration",
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                )
            )
        return render_template(
            "user/registration/update/field/fname.html",
            edition=payload["edition"],
            pfname=professor.fname,
            student=student,
            form=form,
        )
    return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/students/update/<cpfnr>/birth", methods=["GET", "POST"]
)
@login_required
def edit_student_birth(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        student = db.first_or_404(
            sa.select(Student).where(Student.cpfnr == cpfnr)
        )
        form = edit_student_birth_form(
            birth=date_strfmt(student.birth, "dd-mm-yyyy")
        )
        if form.validate_on_submit():
            student.birth = date_strfmt(form.birth.data, "yyyymmdd")
            db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_registration",
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                )
            )
        return render_template(
            "user/registration/update/field/birth.html",
            edition=payload["edition"],
            pfname=professor.fname,
            student=student,
            form=form,
        )
    return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/students/update/<cpfnr>/email", methods=["GET", "POST"]
)
@login_required
def edit_student_email(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        student = db.first_or_404(
            sa.select(Student).where(Student.cpfnr == cpfnr)
        )
        form = edit_student_email_form(email=student.email)
        if form.validate_on_submit():
            student.email = form.email.data
            db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_registration",
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                )
            )
        return render_template(
            "user/registration/update/field/email.html",
            edition=payload["edition"],
            pfname=professor.fname,
            student=student,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/student/enrollment/update/request")
@login_required
def request_student_enrollment_edition(taxnr):
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
            "user/enrollment/update/request.html",
            payload=payload,
            pfname=professor.fname,
            enrollments=enrollments,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/enrollment/update/<cpfnr>",
    methods=["GET", "POST"],
)
@login_required
def edit_student_enrollment(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        student = db.first_or_404(
            sa.select(Student).where(Student.cpfnr == cpfnr)
        )
        enrollment = db.first_or_404(
            sa.select(Enrollment).where(
                Enrollment.cpfnr == cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
            )
        )
        school = db.first_or_404(
            sa.select(School).where(School.inep == enrollment.inep)
        )
        return render_template(
            "user/enrollment/update/enrollment.html",
            payload=payload,
            pfname=professor.fname,
            student=student,
            enrollment=enrollment,
            school=school,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/enrollment/update/<cpfnr>/inep",
    methods=["GET", "POST"],
)
@login_required
def edit_enrollment_inep(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        student = db.first_or_404(
            sa.select(Student).where(Student.cpfnr == cpfnr)
        )
        enrollment = db.first_or_404(
            sa.select(Enrollment).where(
                Enrollment.cpfnr == cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
            )
        )
        form = edit_enrollment_inep_form(inep=enrollment.inep)
        if form.validate_on_submit():
            enrollment.inep = form.inep.data
            db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_enrollment",
                    payload=payload,
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                    student=student,
                )
            )
        return render_template(
            "user/enrollment/update/field/inep.html",
            payload=payload,
            pfname=professor.fname,
            student=student,
            cpfnr=cpfnr,
            enrollment=enrollment,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/enrollment/update/<cpfnr>/roll",
    methods=["GET", "POST"],
)
@login_required
def edit_enrollment_roll(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        student = db.first_or_404(
            sa.select(Student).where(Student.cpfnr == cpfnr)
        )
        enrollment = db.first_or_404(
            sa.select(Enrollment).where(
                Enrollment.cpfnr == cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
            )
        )
        form = edit_enrollment_roll_form(roll=enrollment.roll)
        if form.validate_on_submit():
            enrollment.roll = form.roll.data
            db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_enrollment",
                    payload=payload,
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                    student=student,
                )
            )
        return render_template(
            "user/enrollment/update/field/roll.html",
            payload=payload,
            pfname=professor.fname,
            student=student,
            cpfnr=cpfnr,
            enrollment=enrollment,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/enrollment/update/<cpfnr>/need",
    methods=["GET", "POST"],
)
@login_required
def edit_enrollment_need(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        student = db.first_or_404(
            sa.select(Student).where(Student.cpfnr == cpfnr)
        )
        enrollment = db.first_or_404(
            sa.select(Enrollment).where(
                Enrollment.cpfnr == cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
            )
        )
        form = edit_enrollment_need_form(need=enrollment.need)
        if form.validate_on_submit():
            enrollment.need = re.sub(
                r"\s+", r" ", unidecode(form.need.data.lower())
            )
            db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_enrollment",
                    payload=payload,
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                    student=student,
                )
            )
        return render_template(
            "user/enrollment/update/field/need.html",
            payload=payload,
            pfname=professor.fname,
            student=student,
            cpfnr=cpfnr,
            enrollment=enrollment,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))
