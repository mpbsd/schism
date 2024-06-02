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
from omeg.data.load import CPF, DATE
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
        date = DATE(birth.data)
        cond_1 = date.exists() is True
        cond_2 = date.is_not_in_the_future() is True
        cond_3 = date.year_belongs_to_selected_range() is True
        if (cond_1 and cond_2 and cond_3) is False:
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
        date = DATE(birth.data)
        cond_1 = date.exists() is True
        cond_2 = date.is_not_in_the_future() is True
        cond_3 = date.year_belongs_to_selected_range() is True
        if (cond_1 and cond_2 and cond_3) is False:
            raise ValidationError("Data incorreta")


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
