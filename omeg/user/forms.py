import re

import sqlalchemy as sa
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    NumberRange,
    ValidationError,
)

from omeg.conf.boost import db
from omeg.data.load import CPF
from omeg.mold.models import Professor, School, Student


class student_registration_form(FlaskForm):
    cpfnr = StringField("CPF", validators=[DataRequired()])
    fname = StringField("Nome completo", validators=[DataRequired()])
    birth = StringField("Data de nascimento", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    roll = IntegerField("Nível", validators=[NumberRange(min=1, max=3)])
    inep = StringField("Código INEP", validators=[DataRequired()])
    need = StringField("Condições especiais para participar das provas")
    submit = SubmitField("Cadastrar")

    def validate_cpfnr(self, cpfnr):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.taxnr == cpfnr.data)
        )
        student = db.session.scalar(
            sa.select(Student).where(Student.cpfnr == cpfnr.data)
        )
        if CPF(cpfnr.data).digits_match() is False:
            raise ValidationError("CPF inconsistente")
        elif (professor is not None) or (student is not None):
            raise ValidationError("CPF já existe em nosso banco de dados")

    def validate_email(self, email):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.email == email.data)
        )
        student = db.session.scalar(
            sa.select(Student).where(Student.email == email.data)
        )
        if (professor is not None) or (student is not None):
            raise ValidationError("Email já existe em nosso banco de dados")

    def validate_birth(self, birth):
        ndays = {
            1: 31,
            2: 28,
            3: 31,
            4: 30,
            5: 31,
            6: 30,
            7: 31,
            8: 31,
            9: 30,
            10: 31,
            11: 30,
            12: 31,
        }
        re_d = r"0[1-9]|[12][0-9]|3[01]"
        re_m = r"0[1-9]|1[012]"
        re_y = r"20[01][0-9]"
        re_1 = re.compile(r"(%s)[/-]?(%s)[/-]?(%s)" % (re_d, re_m, re_y))
        re_2 = re.compile(r"(%s)[/-]?(%s)[/-]?(%s)" % (re_y, re_m, re_d))
        is_real_date = False
        if re_1.match(birth.data) or re_2.match(birth.data):
            if re_1.match(birth.data):
                D = re_1.match(birth.data)
                d = int(D.group(1))
                m = int(D.group(2))
                y = int(D.group(3))
            elif re_2.match(birth.data):
                D = re_2.match(birth.data)
                d = int(D.group(3))
                m = int(D.group(2))
                y = int(D.group(1))
            if (m == 2) and ((y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)):
                ndays[m] += 1
            if d <= ndays[m]:
                is_real_date = True
        if is_real_date is False:
            raise ValidationError("Data incorreta")

    def validate_inep(self, inep):
        school = db.session.scalar(
            sa.select(School).where(School.inep == inep.data)
        )
        if school is None:
            raise ValidationError("Código INEP incorreto")


class edit_student_cpfnr_form(FlaskForm):
    cpfnr = StringField("CPF", validators=[DataRequired()])
    submit = SubmitField("Confirmar")

    def validate_cpfnr(self, cpfnr):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.taxnr == cpfnr.data)
        )
        student = db.session.scalar(
            sa.select(Student).where(Student.cpfnr == cpfnr.data)
        )
        if CPF(cpfnr.data).digits_match() is False:
            raise ValidationError("CPF inconsistente")
        elif (professor is not None) or (student is not None):
            raise ValidationError("CPF já existe em nosso banco de dados")


class edit_student_fname_form(FlaskForm):
    fname = StringField("Nome completo", validators=[DataRequired()])
    submit = SubmitField("Confirmar")


class edit_student_birth_form(FlaskForm):
    birth = StringField("Data de nascimento", validators=[DataRequired()])
    submit = SubmitField("Confirmar")

    def validate_birth(self, birth):
        ndays = {
            1: 31,
            2: 28,
            3: 31,
            4: 30,
            5: 31,
            6: 30,
            7: 31,
            8: 31,
            9: 30,
            10: 31,
            11: 30,
            12: 31,
        }
        re_d = r"0[1-9]|[12][0-9]|3[01]"
        re_m = r"0[1-9]|1[012]"
        re_y = r"20[01][0-9]"
        re_1 = re.compile(r"(%s)[/-]?(%s)[/-]?(%s)" % (re_d, re_m, re_y))
        re_2 = re.compile(r"(%s)[/-]?(%s)[/-]?(%s)" % (re_y, re_m, re_d))
        is_real_date = False
        if re_1.match(birth.data) or re_2.match(birth.data):
            if re_1.match(birth.data):
                D = re_1.match(birth.data)
                d = int(D.group(1))
                m = int(D.group(2))
                y = int(D.group(3))
            elif re_2.match(birth.data):
                D = re_2.match(birth.data)
                d = int(D.group(3))
                m = int(D.group(2))
                y = int(D.group(1))
            if (m == 2) and ((y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)):
                ndays[m] += 1
            if d <= ndays[m]:
                is_real_date = True
        if is_real_date is False:
            raise ValidationError("Data inexistente")


class edit_student_email_form(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Confirmar")

    def validate_email(self, email):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.email == email.data)
        )
        student = db.session.scalar(
            sa.select(Student).where(Student.email == email.data)
        )
        if (professor is not None) or (student is not None):
            raise ValidationError("Email já existe em nosso banco de dados")


class edit_enrollment_inep_form(FlaskForm):
    inep = StringField("Código INEP", validators=[DataRequired()])
    submit = SubmitField("Confirmar")

    def validate_inep(self, inep):
        school = db.session.scalar(
            sa.select(School).where(School.inep == inep.data)
        )
        if school is None:
            raise ValidationError("Código INEP incorreto")


class edit_enrollment_roll_form(FlaskForm):
    roll = IntegerField("Nível", validators=[NumberRange(min=1, max=3)])
    submit = SubmitField("Confirmar")


class edit_enrollment_need_form(FlaskForm):
    need = StringField("Condições especiais para participar das provas")
    submit = SubmitField("Cadastrar")
