import re

import sqlalchemy as sa
from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from unidecode import unidecode

from omeg.auth.emails import send_enrollment_confirmation_email
from omeg.conf.boost import db
from omeg.data.load import CPF, DATE, payload
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


@bp_user_routes.route("/professor/<taxnr>/dashboard")
@login_required
def professor_dashboard(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        return render_template(
            "user/dashboard.html",
            edition=payload["edition"],
            save_the_date=payload["save_the_date"],
            days_until=payload["days_until"],
            pfname=professor.fname,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/save_the_date")
@login_required
def save_the_date(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        return render_template(
            "user/utils/save_the_date.html",
            edition=payload["edition"],
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
            edition=payload["edition"],
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
            cpfnr = CPF(form.cpfnr.data).strfmt("raw")
            student = Student(
                cpfnr=cpfnr,
                fname=re.sub(r"\s+", r" ", form.fname.data),
                birth=DATE(form.birth.data).isofmt(),
                email=form.email.data,
            )
            enrollment = Enrollment(
                cpfnr=cpfnr,
                taxnr=taxnr,
                inep=form.inep.data,
                year=payload["edition"],
                roll=form.roll.data,
                need=re.sub(r"\s+", r" ", unidecode(form.need.data.lower())),
                gift="N",
            )
            cpfnr_medalists_last_edition = [
                cpfnr
                for (cpfnr,) in db.session.query(Enrollment.cpfnr)
                .where(
                    Enrollment.gift.op("REGEXP")("[OoPpBb]"),
                    Enrollment.year == payload["edition"] - 1,
                )
                .all()
            ]
            medalists_currently_enrolled = [
                cpfnr
                for (cpfnr,) in db.session.query(Enrollment.cpfnr)
                .where(
                    Enrollment.inep == enrollment.inep,
                    Enrollment.year == payload["edition"],
                )
                .all()
                if cpfnr in cpfnr_medalists_last_edition
            ]
            quota = len(
                [
                    cpfnr
                    for (cpfnr,) in db.session.query(Enrollment.cpfnr)
                    .where(
                        Enrollment.inep == enrollment.inep,
                        Enrollment.year == payload["edition"],
                        Enrollment.roll == enrollment.roll,
                    )
                    .all()
                    if cpfnr not in medalists_currently_enrolled
                ]
            )
            # if the quota is less than or equal to or the cpfnr belongs to a
            # certain list, pass.
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
                return redirect(
                    url_for(
                        "bp_user_routes.registered_students",
                        taxnr=taxnr,
                    )
                )
            else:
                extract = students_extract_query(professor.taxnr)
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


@bp_user_routes.route("/professor/<taxnr>/students/overview")
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
            CPF=CPF,
            DATE=DATE,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/enrollments/overview")
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
            CPF=CPF,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/enrollments/extract")
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
            CPF=CPF,
            DATE=DATE,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/student/<cpfnr>/registration/update",
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
            CPF=CPF,
            DATE=DATE,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/student/<cpfnr>/registration/update/cpfnr",
    methods=["GET", "POST"],
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
        form = edit_student_cpfnr_form(cpfnr=cpfnr)
        if form.validate_on_submit():
            student.cpfnr = CPF(form.cpfnr.data).strfmt("raw")
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
            sfname=student.fname,
            cpfnr=cpfnr,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/student/<cpfnr>/registration/update/fname",
    methods=["GET", "POST"],
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
            sfname=student.fname,
            cpfnr=cpfnr,
            form=form,
        )
    return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/student/<cpfnr>/registration/update/birth",
    methods=["GET", "POST"],
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
            birth=DATE(student.birth).strfmt("dd-mm-yyyy")
        )
        if form.validate_on_submit():
            student.birth = DATE(form.birth.data).isofmt()
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
            sfname=student.fname,
            cpfnr=cpfnr,
            form=form,
        )
    return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/student/<cpfnr>/registration/update/email",
    methods=["GET", "POST"],
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
            sfname=student.fname,
            cpfnr=cpfnr,
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
                Enrollment.year == payload["edition"],
                Student.cpfnr == Enrollment.cpfnr,
                School.inep == Enrollment.inep,
            )
            .order_by(Enrollment.roll)
            .all()
        )
        return render_template(
            "user/enrollment/update/request.html",
            edition=payload["edition"],
            pfname=professor.fname,
            enrollments=enrollments,
            CPF=CPF,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/student/<cpfnr>/enrollment/update",
    methods=["GET", "POST"],
)
@login_required
def edit_student_enrollment(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        enrollment = (
            db.session.query(
                Student.fname,
                Enrollment.inep,
                Enrollment.roll,
                Enrollment.need,
                School.name,
            )
            .where(
                Enrollment.taxnr == taxnr,
                Enrollment.cpfnr == cpfnr,
                Enrollment.year == payload["edition"],
                School.inep == Enrollment.inep,
                Student.cpfnr == Enrollment.cpfnr,
            )
            .first()
        )
        return render_template(
            "user/enrollment/update/enrollment.html",
            edition=payload["edition"],
            pfname=professor.fname,
            cpfnr=cpfnr,
            enrollment=enrollment,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/student/<cpfnr>/enrollment/update/inep",
    methods=["GET", "POST"],
)
@login_required
def edit_enrollment_inep(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        students_enrollment = (
            db.session.query(
                Student.fname,
                Enrollment.inep,
                Enrollment.roll,
            )
            .where(
                Enrollment.cpfnr == cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
                Student.cpfnr == Enrollment.cpfnr,
            )
            .first()
        )
        form = edit_enrollment_inep_form(inep=students_enrollment.inep)
        if form.validate_on_submit():
            enrollment = (
                db.session.query(Enrollment)
                .where(
                    Enrollment.cpfnr == cpfnr,
                    Enrollment.taxnr == taxnr,
                    Enrollment.year == payload["edition"],
                )
                .first()
            )
            quota = (
                db.session.query(Enrollment)
                .where(
                    Enrollment.inep == form.inep.data,
                    Enrollment.year == payload["edition"],
                    Enrollment.roll == students_enrollment.roll,
                )
                .count()
            )
            if quota <= payload["quota"] - 1:
                enrollment.inep = form.inep.data
                db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_enrollment",
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                )
            )
        return render_template(
            "user/enrollment/update/field/inep.html",
            edition=payload["edition"],
            pfname=professor.fname,
            sfname=students_enrollment.fname,
            cpfnr=cpfnr,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/student/<cpfnr>/enrollment/update/roll",
    methods=["GET", "POST"],
)
@login_required
def edit_enrollment_roll(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        students_enrollment = (
            db.session.query(
                Student.fname,
                Enrollment.roll,
            )
            .where(
                Enrollment.cpfnr == cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
                Student.cpfnr == Enrollment.cpfnr,
            )
            .first()
        )
        form = edit_enrollment_roll_form(roll=students_enrollment.roll)
        if form.validate_on_submit():
            enrollment = (
                db.session.query(Enrollment)
                .where(
                    Enrollment.cpfnr == cpfnr,
                    Enrollment.taxnr == taxnr,
                    Enrollment.year == payload["edition"],
                )
                .first()
            )
            quota = (
                db.session.query(Enrollment)
                .where(
                    Enrollment.inep == enrollment.inep,
                    Enrollment.year == payload["edition"],
                    Enrollment.roll == form.roll.data,
                )
                .count()
            )
            if quota <= payload["quota"] - 1:
                enrollment.roll = form.roll.data
                db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_enrollment",
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                )
            )
        return render_template(
            "user/enrollment/update/field/roll.html",
            edition=payload["edition"],
            pfname=professor.fname,
            sfname=students_enrollment.fname,
            cpfnr=cpfnr,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/student/<cpfnr>/enrollment/update/need",
    methods=["GET", "POST"],
)
@login_required
def edit_enrollment_need(taxnr, cpfnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        students_enrollment = (
            db.session.query(
                Student.fname,
                Enrollment.need,
            )
            .where(
                Enrollment.cpfnr == cpfnr,
                Enrollment.taxnr == taxnr,
                Enrollment.year == payload["edition"],
                Student.cpfnr == Enrollment.cpfnr,
            )
            .first()
        )
        form = edit_enrollment_need_form(need=students_enrollment.need)
        if form.validate_on_submit():
            enrollment = (
                db.session.query(Enrollment)
                .where(
                    Enrollment.cpfnr == cpfnr,
                    Enrollment.taxnr == taxnr,
                    Enrollment.year == payload["edition"],
                )
                .first()
            )
            enrollment.need = re.sub(
                r"\s+", r" ", unidecode(form.need.data.lower())
            )
            db.session.commit()
            return redirect(
                url_for(
                    "bp_user_routes.edit_student_enrollment",
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                )
            )
        return render_template(
            "user/enrollment/update/field/need.html",
            edition=payload["edition"],
            pfname=professor.fname,
            sfname=students_enrollment.fname,
            cpfnr=cpfnr,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route("/professor/<taxnr>/enrollments/past-seven-years")
@login_required
def show_enrollments_the_past_seven_years(taxnr):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        enrollments_from_the_last_seven_years = (
            db.session.query(
                Student.cpfnr,
                Student.fname,
                Student.birth,
                Student.email,
                School.inep,
                School.name,
                Enrollment.year,
                Enrollment.roll,
                Enrollment.need,
            )
            .where(
                School.inep == Enrollment.inep,
                Student.cpfnr == Enrollment.cpfnr,
                Enrollment.year >= payload["edition"] - 7,
            )
            .all()
        )
        enrollments_from_this_year = [
            enrollment.cpfnr
            for enrollment in db.session.query(Enrollment.cpfnr)
            .where(
                Enrollment.year == payload["edition"],
            )
            .all()
        ]
        enrollments = sorted(
            [
                enrollment
                for enrollment in enrollments_from_the_last_seven_years
                if enrollment.cpfnr not in enrollments_from_this_year
            ],
            key=lambda x: x.fname,
        )
        return render_template(
            "user/enrollment/read/past_seven_years.html",
            edition=payload["edition"],
            pfname=professor.fname,
            enrollments=enrollments,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/enrollments/new-from-previous"
    "/<cpfnr>/<fname>/<birth>/<email>/<inep>/<name>/<year>/<roll>"
)
@login_required
def new_enrollment_from_previous_one(
    taxnr, cpfnr, fname, birth, email, inep, name, year, roll
):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        return render_template(
            "user/enrollment/create/confirm.html",
            edition=payload["edition"],
            taxnr=taxnr,
            pfname=professor.fname,
            cpfnr=cpfnr,
            fname=fname,
            birth=birth,
            email=email,
            inep=inep,
            name=name,
            year=year,
            roll=roll,
            CPF=CPF,
            DATE=DATE,
            send_email=send_enrollment_confirmation_email,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/enrollments/new-from-previous"
    "/<cpfnr>/<fname>/<birth>/<email>/<inep>/<name>/<year>/<roll>"
    "/edit-inep",
    methods=["GET", "POST"],
)
@login_required
def edit_inep_for_new_enrollment(
    taxnr, cpfnr, fname, birth, email, inep, name, year, roll
):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        form = edit_enrollment_inep_form(inep=inep)
        if form.validate_on_submit():
            school_name = (
                db.session.query(School.name)
                .where(School.inep == form.inep.data)
                .first()
            )
            return redirect(
                url_for(
                    "bp_user_routes.new_enrollment_from_previous_one",
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                    fname=fname,
                    birth=birth,
                    email=email,
                    inep=form.inep.data,
                    name=school_name[0],
                    year=year,
                    roll=roll,
                )
            )
        return render_template(
            "user/enrollment/update/field/inep.html",
            edition=payload["edition"],
            pfname=professor.fname,
            sfname=fname,
            cpfnr=cpfnr,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))


@bp_user_routes.route(
    "/professor/<taxnr>/enrollments/new-from-previous"
    "/<cpfnr>/<fname>/<birth>/<email>/<inep>/<name>/<year>/<roll>"
    "/edit-roll",
    methods=["GET", "POST"],
)
@login_required
def edit_roll_for_new_enrollment(
    taxnr, cpfnr, fname, birth, email, inep, name, year, roll
):
    if taxnr == current_user.taxnr:
        professor = db.first_or_404(
            sa.select(Professor).where(Professor.taxnr == taxnr)
        )
        form = edit_enrollment_roll_form(roll=roll)
        if form.validate_on_submit():
            return redirect(
                url_for(
                    "bp_user_routes.new_enrollment_from_previous_one",
                    taxnr=taxnr,
                    cpfnr=cpfnr,
                    fname=fname,
                    birth=birth,
                    email=email,
                    inep=inep,
                    name=name,
                    year=year,
                    roll=form.roll.data,
                )
            )
        return render_template(
            "user/enrollment/update/field/roll.html",
            edition=payload["edition"],
            pfname=professor.fname,
            sfname=fname,
            cpfnr=cpfnr,
            form=form,
        )
    else:
        return redirect(url_for("bp_home_routes.home"))
