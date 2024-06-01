import re
from datetime import date


class CPF:
    def __init__(self, cpfnr: str):
        self.cpfnr = cpfnr

    def strfmt(self, fmt: str) -> str:
        re_cpfnr = re.compile(r"(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})")
        cpfnrfmt = {
            "raw": re_cpfnr.sub(r"\1\2\3\4", self.cpfnr),
            "dot": re_cpfnr.sub(r"\1.\2.\3-\4", self.cpfnr),
        }
        return cpfnrfmt[fmt]

    def digits_match(self) -> bool:
        CPF = self.strfmt("raw")
        B = False
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

    def __repr__(self):
        return self.strfmt("dot")


def date_strfmt(date, style):
    STYLE = {
        "dd-mm-yyyy": "%02d-%02d-%04d",
        "dd/mm/yyyy": "%02d/%02d/%04d",
        "yyyy-mm-dd": "%04d-%02d-%02d",
        "yyyy/mm/dd": "%04d/%02d/%02d",
        "yyyymmdd": "%04d%02d%02d",
    }
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
        if style in ["dd-mm-yyyy", "dd/mm/yyyy"]:
            Dfmt = STYLE[style] % (d, m, y)
        else:
            Dfmt = STYLE[style] % (y, m, d)
    return Dfmt


def beancount(dt1, dt2):
    if dt1 < dt2:
        beans = f"{(dt2 - dt1).days} dias"
    else:
        beans = "---"
    return beans


payload = {
    "edition": 2024,
    "quota": 10,
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
            "opening": beancount(date.today(), date.fromisoformat("20240615")),
            "closing": beancount(date.today(), date.fromisoformat("20240715")),
        },
        "step": {
            "1": beancount(date.today(), date.fromisoformat("20240914")),
            "2": beancount(date.today(), date.fromisoformat("20241005")),
        },
    },
}
