import re

import sqlalchemy as sa
from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    ValidationError,
)

from omeg.conf.boost import db
from omeg.data.load import cpf_digits_match
from omeg.mold.models import Professor, School, Student


class professor_registration_request_form(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Enviar Link")


class professor_registration_form(FlaskForm):
    taxnr = StringField("CPF", validators=[DataRequired()])
    fname = StringField("Nome", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password1 = PasswordField(
        "Senha", validators=[DataRequired(), Length(min=8, max=32)]
    )
    password2 = PasswordField(
        "Confirmar a senha", validators=[DataRequired(), EqualTo("password1")]
    )
    submit = SubmitField("Registrar-se")

    def validate_taxnr(self, taxnr):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.taxnr == taxnr.data)
        )
        if cpf_digits_match(taxnr.data) is False:
            raise ValidationError("CPF inconsistente")
        elif professor is not None:
            raise ValidationError("CPF já existe em nosso banco de dados")

    def validate_mail(self, email):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.email == email.data)
        )
        if professor is not None:
            raise ValidationError("Email já cadastrado")


class login_form(FlaskForm):
    taxnr = StringField("CPF", validators=[DataRequired()])
    password = PasswordField("Senha", validators=[DataRequired()])
    # remember_me = BooleanField("Permanecer conectado")
    submit = SubmitField("Acessar")


class reset_password_request_form(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Enviar Link")


class reset_password_form(FlaskForm):
    password1 = PasswordField("Nova senha", validators=[DataRequired()])
    password2 = PasswordField(
        "Confirme a senha", validators=[DataRequired(), EqualTo("password1")]
    )
    submit = SubmitField("Alterar")


class student_registration_form(FlaskForm):
    cpfnr = StringField("CPF", validators=[DataRequired()])
    fname = StringField("Nome", validators=[DataRequired()])
    birth = StringField("Data de nascimento", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    roll = IntegerField("Nível", validators=[NumberRange(min=1, max=3)])
    inep = StringField("Codigo INEP", validators=[DataRequired()])
    submit = SubmitField("Cadastrar")

    def validate_cpfnr(self, cpfnr):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.taxnr == cpfnr.data)
        )
        student = db.session.scalar(
            sa.select(Student).where(Student.cpfnr == cpfnr.data)
        )
        if cpf_digits_match(cpfnr.data) is False:
            raise ValidationError("CPF inconsistente")
        elif professor is not None:
            raise ValidationError("CPF já existe em nosso banco de dados")
        elif student is not None:
            raise ValidationError("CPF já existe em nosso banco de dados")

    def validate_mail(self, email):
        student = db.session.scalar(
            sa.select(Student).where(Student.email == email.data)
        )
        if student is not None:
            raise ValidationError("Email já cadastrado")

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
        re_day = r"(0[1-9]|[12][0-9]|3[01])"
        re_month = r"(0[1-9]|1[012])"
        re_year = r"(20(0[4-9]|1[0-3]))"
        re_date = re.compile(re_year + re_month + re_day)
        is_real_date = False
        if re_date.match(birth.data):
            date = re_date.match(birth.data)
            d = int(date.group(4))
            m = int(date.group(3))
            y = int(date.group(1))
            if (m == 2) and ((y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)):
                ndays[m] += 1
            if d <= ndays[m]:
                is_real_date = True
        if is_real_date is False:
            raise ValidationError("Data inexistente ou fora do intervalo")

    def validate_inep(self, inep):
        school = db.session.scalar(
            sa.select(School).where(School.inep == inep.data)
        )
        if school is None:
            raise ValidationError("Código INEP incorreto")
