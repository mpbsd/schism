from flask import current_app, render_template

from omeg.conf.boost import send_email
from omeg.data.load import CPF, DATE
from omeg.mold.models import Enrollment


def send_enrollment_confirmation_email(
    taxnr,
    pfname,
    cpfnr,
    sfname,
    birth,
    semail,
    inep,
    name,
    roll,
):
    token = Enrollment.get_enrollment_request_token(
        taxnr,
        pfname,
        cpfnr,
        sfname,
        birth,
        semail,
        inep,
        name,
        roll,
    )
    send_email(
        "[OMEG] Inscrição na Olimpíada de Matemática do Estado de Goiás",
        sender=current_app.config["ADMINS"][0],
        recipients=[semail],
        text_body=render_template(
            "user/enrollment/create/mail.txt",
            taxnr=taxnr,
            pfname=pfname,
            cpfnr=cpfnr,
            sfname=sfname,
            birth=birth,
            semail=semail,
            inep=inep,
            name=name,
            roll=roll,
            token=token,
            CPF=CPF,
            DATE=DATE,
        ),
        html_body=render_template(
            "user/enrollment/create/mail.html",
            taxnr=taxnr,
            pfname=pfname,
            cpfnr=cpfnr,
            sfname=sfname,
            birth=birth,
            semail=semail,
            inep=inep,
            name=name,
            roll=roll,
            token=token,
            CPF=CPF,
            DATE=DATE,
        ),
    )
