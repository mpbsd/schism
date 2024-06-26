import sqlalchemy as sa
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError,
)

from omeg.conf.boost import db
from omeg.data.load import CPF
from omeg.mold.models import Professor


class professor_registration_request_form(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Email(message="Email inválido"),
        ],
    )
    submit = SubmitField("Enviar Link")


class professor_registration_form(FlaskForm):
    taxnr = StringField(
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
        "Nome",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=5,
                max=255,
                message="Informe o nome completo do professsor",
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
    password1 = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=8,
                max=32,
                message="A senha deve ter entre 8 e 32 caracteres",
            ),
        ],
    )
    password2 = PasswordField(
        "Confirme a senha",
        validators=[
            DataRequired(message="Campo obrigatório"),
            EqualTo("password1", message="As senhas devem coincidir"),
        ],
    )
    submit = SubmitField("Registrar-se")

    def validate_taxnr(self, taxnr):
        professor = db.session.scalar(
            sa.select(Professor).where(Professor.taxnr == taxnr.data)
        )
        if CPF(taxnr.data).digits_match() is False:
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
    taxnr = StringField(
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
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Campo obrigatório"),
        ],
    )
    submit = SubmitField("Acessar")


class reset_password_request_form(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Email(message="Email inválido"),
        ],
    )
    submit = SubmitField("Enviar Link")


class reset_password_form(FlaskForm):
    password1 = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Campo obrigatório"),
            Length(
                min=8,
                max=32,
                message="A senha deve ter entre 8 e 32 caracteres",
            ),
        ],
    )
    password2 = PasswordField(
        "Confirme a senha",
        validators=[
            DataRequired(message="Campo obrigatório"),
            EqualTo("password1", message="As senhas devem coincidir"),
        ],
    )
    submit = SubmitField("Alterar")
