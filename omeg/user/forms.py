import sqlalchemy as sa
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    ValidationError,
)

from omeg.conf.boost import db
from omeg.data.load import CPF, DATE
from omeg.mold.models import Professor, School, Student


class student_registration_form(FlaskForm):
    cpfnr = StringField(
        "CPF",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=11,
                max=14,
                message="CPF é composto por 11 dígitos e pode conter ou não "
                "os caracteres . (ponto) e - (traço)",
            ),
        ],
    )
    fname = StringField(
        "Nome completo",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=5,
                max=255,
                message="Informe o nome completo do estudante",
            ),
        ],
    )
    birth = StringField(
        "Data de nascimento",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=8,
                max=10,
                message="São 8 dígitos. Pode-se usar / (barra) e/ou - (traço) "
                "como separador entre os campos",
            ),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Email(message="Email inválido"),
        ],
    )
    roll = IntegerField(
        "Nível",
        validators=[
            NumberRange(min=1, max=3, message="Deve ser igual a 1, 2 ou 3")
        ],
    )
    inep = StringField(
        "Código INEP", validators=[DataRequired(message="Campo obrigatório")]
    )
    need = StringField(
        "Condições especiais para participar das provas",
        validators=[Length(max=255, message="Máximo de 255 caracteres")],
    )
    submit = SubmitField("Cadastrar")

    def validate_cpfnr(self, cpfnr):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.taxnr == cpfnr.data)
        )
        student = db.session.scalar(
            sa.select(Student).where(Student.cpfnr == cpfnr.data)
        )
        if not CPF(cpfnr.data).digits_match():
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
        cond_1 = date.exists()
        cond_2 = date.is_not_in_the_future()
        cond_3 = date.year_belongs_to_selected_range()
        if not (cond_1 and cond_2 and cond_3):
            raise ValidationError("Data incorreta")

    def validate_inep(self, inep):
        school = db.session.scalar(
            sa.select(School).where(School.inep == inep.data)
        )
        if school is None:
            raise ValidationError("Código INEP incorreto")


class edit_student_cpfnr_form(FlaskForm):
    cpfnr = StringField(
        "CPF",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=11,
                max=14,
                message="CPF é composto por 11 dígitos e pode conter ou não "
                "os caracteres . (ponto) e - (traço)",
            ),
        ],
    )
    submit = SubmitField("Confirmar")

    def validate_cpfnr(self, cpfnr):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.taxnr == cpfnr.data)
        )
        student = db.session.scalar(
            sa.select(Student).where(Student.cpfnr == cpfnr.data)
        )
        if not CPF(cpfnr.data).digits_match():
            raise ValidationError("CPF inconsistente")
        elif (professor is not None) or (student is not None):
            raise ValidationError("CPF já existe em nosso banco de dados")


class edit_student_fname_form(FlaskForm):
    fname = StringField(
        "Nome completo",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=5,
                max=255,
                message="Informe o nome completo do estudante",
            ),
        ],
    )
    submit = SubmitField("Confirmar")


class edit_student_birth_form(FlaskForm):
    birth = StringField(
        "Data de nascimento",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=8,
                max=10,
                message="Sao 8 digitos. Pode-se usar / (barra) e/ou - (traço) "
                "como separador entre os campos",
            ),
        ],
    )
    submit = SubmitField("Confirmar")

    def validate_birth(self, birth):
        date = DATE(birth.data)
        cond_1 = date.exists()
        cond_2 = date.is_not_in_the_future()
        cond_3 = date.year_belongs_to_selected_range()
        if not (cond_1 and cond_2 and cond_3):
            raise ValidationError("Data incorreta")


class edit_student_email_form(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Email(message="Email inválido"),
        ],
    )
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
    inep = StringField(
        "Código INEP", validators=[DataRequired(message="Campo obrigatório")]
    )
    submit = SubmitField("Confirmar")

    def validate_inep(self, inep):
        school = db.session.scalar(
            sa.select(School).where(School.inep == inep.data)
        )
        if school is None:
            raise ValidationError("Código INEP incorreto")


class edit_enrollment_roll_form(FlaskForm):
    roll = IntegerField(
        "Nível",
        validators=[
            NumberRange(min=1, max=3, message="Deve ser igual a 1, 2 ou 3")
        ],
    )
    submit = SubmitField("Confirmar")


class edit_enrollment_need_form(FlaskForm):
    need = StringField(
        "Condições especiais para participar das provas",
        validators=[Length(max=255, message="máximo de 255 caracteres")],
    )
    submit = SubmitField("Cadastrar")


class find_enrollment_by_cpfnr(FlaskForm):
    cpfnr = StringField(
        "CPF do estudante",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=11,
                max=14,
                message="CPF é composto por 11 dígitos e pode conter ou não "
                "os caracteres . (ponto) e - (traço)",
            ),
        ],
    )
    submit = SubmitField("Buscar")


class new_enrollment_from_a_previous_one_form(FlaskForm):
    confirmation = StringField(
        "Enviar email de confirmação para o estudante?",
        validators=[DataRequired("Campo obrigatório")],
    )
    submit = SubmitField("Enviar Email")

    def validate_confirmation(self, confirmation):
        if confirmation.data.lower() != "sim":
            raise ValidationError("Responda 'Sim' e clique em 'Enviar Email'")


class confirm_new_enrollment_from_a_previous_one_form(FlaskForm):
    confirmation = StringField(
        "Deseja se inscrever na OMEG utilizando os dados acima?",
        validators=[DataRequired("Campo obrigatório")],
    )
    submit = SubmitField("Confirmar")

    def validate_confirmation(self, confirmation):
        if confirmation.data.lower() != "sim":
            raise ValidationError("Responda 'Sim' e clique em 'Inscrever'")
