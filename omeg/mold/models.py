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
    inep: so.Mapped[str] = so.mapped_column(sa.Integer, primary_key=True)
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
    cpfP: so.Mapped[str] = so.mapped_column(sa.String(11), primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(255))
    mail: so.Mapped[str] = so.mapped_column(
        sa.String(255), index=True, unique=True
    )
    hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255))

    def set_password(self, password):
        self.hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hash, password)

    def get_id(self):
        return self.cpfP

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.cpfP, "exp": time() + expires_in},
            Config.SECRET_KEY,
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            cpfP = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])[
                "reset_password"
            ]
        except jwt.exceptions.InvalidTokenError as Err:
            print(Err)
            return None
        return db.session.get(Professor, cpfP)

    @staticmethod
    def get_registration_request_token(mail, expires_in=600):
        return jwt.encode(
            {"mail": mail, "exp": time() + expires_in},
            Config.SECRET_KEY,
            algorithm="HS256",
        )

    @staticmethod
    def verify_registration_request_token(token):
        try:
            mail = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])[
                "mail"
            ]
        except jwt.exceptions.InvalidTokenError as Err:
            print(Err)
            return None
        return mail

    def __repr__(self):
        return f"Professor {self.cpfP}"


class Student(db.Model):
    cpfS: so.Mapped[str] = so.mapped_column(sa.String(11), primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(255))
    bday: so.Mapped[str] = so.mapped_column(sa.Date)
    mail: so.Mapped[str] = so.mapped_column(
        sa.String(255), index=True, unique=True
    )

    def __repr__(self):
        return f"Student {self.cpfS}"


class Enrollment(db.Model):
    cpfS: so.Mapped[str] = so.mapped_column(
        sa.String(11), sa.ForeignKey(Student.cpfS), primary_key=True
    )
    cpfP: so.Mapped[str] = so.mapped_column(
        sa.String(11), sa.ForeignKey(Professor.cpfP), primary_key=True
    )
    inep: so.Mapped[str] = so.mapped_column(
        sa.String(11), sa.ForeignKey(School.inep), primary_key=True
    )
    year: so.Mapped[str] = so.mapped_column(sa.String(11), primary_key=True)
    roll: so.Mapped[int]
    gift: so.Mapped[str] = so.mapped_column(sa.String(6), default="None")

    def __repr__(self):
        return f"{self.cpfS}, {self.inep}, {self.year}, {self.roll}"
