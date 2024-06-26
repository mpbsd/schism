from time import time
from typing import Optional

import jwt
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from omeg.conf.boost import db
from omeg.conf.setup import Config


class School(db.Model):
    inep: so.Mapped[str] = so.mapped_column(sa.String(8), primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(96))
    city: so.Mapped[str] = so.mapped_column(sa.String(27))
    zone: so.Mapped[str] = so.mapped_column(sa.String(6))
    tier: so.Mapped[str] = so.mapped_column(sa.String(7))
    code: so.Mapped[str] = so.mapped_column(sa.String(9))
    pnum: so.Mapped[str] = so.mapped_column(sa.String(14), nullable=True)
    latd: so.Mapped[str] = so.mapped_column(sa.Float, nullable=True)
    lotd: so.Mapped[str] = so.mapped_column(sa.Float, nullable=True)

    def __repr__(self):
        return f"School {self.inep}"


class Professor(UserMixin, db.Model):
    taxnr: so.Mapped[str] = so.mapped_column(sa.String(11), primary_key=True)
    fname: so.Mapped[str] = so.mapped_column(sa.String(255))
    email: so.Mapped[str] = so.mapped_column(
        sa.String(255), index=True, unique=True
    )
    pswrd: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255))

    def set_password(self, password):
        self.pswrd = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pswrd, password)

    def get_id(self):
        return self.taxnr

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.taxnr, "exp": time() + expires_in},
            Config.SECRET_KEY,
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            taxnr = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])[
                "reset_password"
            ]
        except jwt.exceptions.InvalidTokenError as Err:
            print(Err)
            return None
        return db.session.get(Professor, taxnr)

    @staticmethod
    def get_registration_request_token(email, expires_in=600):
        return jwt.encode(
            {"email": email, "exp": time() + expires_in},
            Config.SECRET_KEY,
            algorithm="HS256",
        )

    @staticmethod
    def verify_registration_request_token(token):
        try:
            email = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])[
                "email"
            ]
        except jwt.exceptions.InvalidTokenError as Err:
            print(Err)
            return None
        return email

    def __repr__(self):
        return f"Professor {self.taxnr}"


class Student(db.Model):
    cpfnr: so.Mapped[str] = so.mapped_column(sa.String(11), primary_key=True)
    fname: so.Mapped[str] = so.mapped_column(sa.String(255))
    birth: so.Mapped[str] = so.mapped_column(sa.String(8))
    email: so.Mapped[str] = so.mapped_column(
        sa.String(255), index=True, unique=True
    )

    def __repr__(self):
        return f"Student {self.cpfnr}"


class Enrollment(db.Model):
    cpfnr: so.Mapped[str] = so.mapped_column(
        sa.String(11),
        sa.ForeignKey(Student.cpfnr, onupdate="CASCADE"),
        primary_key=True,
    )
    taxnr: so.Mapped[str] = so.mapped_column(
        sa.String(11),
        sa.ForeignKey(Professor.taxnr, onupdate="CASCADE"),
        primary_key=True,
    )
    inep: so.Mapped[str] = so.mapped_column(
        sa.String(8),
        sa.ForeignKey(School.inep, onupdate="CASCADE"),
        primary_key=True,
    )
    year: so.Mapped[str] = so.mapped_column(sa.String(4), primary_key=True)
    # acceptable values:
    # roll:
    #   '1' meaning 'Sexto e/ou sétimo anos do Ensino Fundamental'
    #   '2' meaning 'Oitavo e/ou nono anos do Ensino Fundamental'
    #   '3' meaning 'Ensino Médio'
    roll: so.Mapped[int]
    need: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=True)
    # acceptable values:
    # gift:
    #   'O' meaning 'Ouro'
    #   'P' meaning 'Prata'
    #   'B' meaning 'Bronze'
    #   'H' meaning 'Honra'
    #   'N' meaning 'Nenhum'
    gift: so.Mapped[chr] = so.mapped_column(sa.CHAR, default="N")

    @staticmethod
    def get_enrollment_request_token(
        taxnr,
        pfname,
        cpfnr,
        sfname,
        birth,
        semail,
        inep,
        name,
        roll,
        expires_in=600,
    ):
        return jwt.encode(
            {
                "taxnr": taxnr,
                "pfname": pfname,
                "cpfnr": cpfnr,
                "sfname": sfname,
                "birth": birth,
                "semail": semail,
                "inep": inep,
                "name": name,
                "roll": roll,
                "exp": time() + expires_in,
            },
            Config.SECRET_KEY,
            algorithm="HS256",
        )

    @staticmethod
    def verify_enrollment_request_token(token):
        try:
            decoded = jwt.decode(
                token, Config.SECRET_KEY, algorithms=["HS256"]
            )
            message = {
                "taxnr": decoded["taxnr"],
                "pfname": decoded["pfname"],
                "cpfnr": decoded["cpfnr"],
                "sfname": decoded["sfname"],
                "birth": decoded["birth"],
                "semail": decoded["semail"],
                "inep": decoded["inep"],
                "name": decoded["name"],
                "roll": decoded["roll"],
            }
        except jwt.exceptions.InvalidTokenError as Err:
            print(Err)
            return None
        return message

    def __repr__(self):
        return f"{self.inep}, {self.cpfnr}, {self.year}, {self.roll}"
