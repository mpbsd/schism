from datetime import date
import re


payload = {
    "edition": 2024,
    "save_the_date": {
        "registration": {
            "opening": date.fromisoformat("20240615"),
            "closing": date.fromisoformat("20240715"),
        },
        "step": {
            "1": date.fromisoformat("20240914"),
            "2": date.fromisoformat("20241005"),
        },
    },
    "days_until": {
        "registration": {
            "opening": (date.fromisoformat("20240615") - date.today()).days,
            "closing": (date.fromisoformat("20240715") - date.today()).days,
        },
        "step": {
            "1": (date.fromisoformat("20240914") - date.today()).days,
            "2": (date.fromisoformat("20241005") - date.today()).days,
        },
    },
}


def cpf_strfmt(cpfnr):
    re_cpf = re.compile(r"(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})")
    return re_cpf.sub(r"\1\2\3\4", cpfnr)


def cpf_digits_match(cpfstr):
    re_cpf = re.compile(r"(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})")
    B = False
    if re_cpf.match(cpfstr):
        CPF = re_cpf.sub(r"\1\2\3\4", cpfstr)
        if CPF != "00000000000":
            D = [0, 0]
            for i in range(9):
                D[0] += (10 - i) * int(CPF[i])
            for i in range(10):
                D[1] += (11 - i) * int(CPF[i])
            D0_is_correct = ((10 * D[0]) % 11) % 10 == int(CPF[9])
            D1_is_correct = ((10 * D[1]) % 11) % 10 == int(CPF[10])
            if D0_is_correct and D1_is_correct:
                B = True
    return B


def date_strfmt(date):
    re_d = r"0[1-9]|[12][0-9]|3[01]"
    re_m = r"0[1-9]|1[012]"
    re_y = r"20[01][0-9]"
    re_1 = re.compile(r"(%s)[/-]?(%s)[/-]?(%s)" % (re_d, re_m, re_y))
    re_2 = re.compile(r"(%s)[/-]?(%s)[/-]?(%s)" % (re_y, re_m, re_d))
    if re_1.match(date) or re_2.match(date):
        if re_1.match(date):
            D = re_1.match(date)
            d = int(D.group(1))
            m = int(D.group(2))
            y = int(D.group(3))
        elif re_2.match(date):
            D = re_2.match(date)
            d = int(D.group(3))
            m = int(D.group(2))
            y = int(D.group(1))
        Dfmt = f"{y}{m}{d}"
    return Dfmt
