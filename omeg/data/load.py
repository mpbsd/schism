import re
from datetime import datetime


class CPF:
    re_cpfnr = re.compile(r"(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})")

    def __init__(self, cpfnr):
        self.cpfnr = cpfnr

    def pattern_match(self):
        B = False
        if len(self.cpfnr) >= 11 and self.re_cpfnr.match(self.cpfnr):
            B = True
        return B

    def strfmt(self, fmt):
        cpf_strfmt = None
        style = {
            "raw": self.re_cpfnr.sub(r"\1\2\3\4", self.cpfnr),
            "fmt": self.re_cpfnr.sub(r"\1.\2.\3-\4", self.cpfnr),
        }
        if self.pattern_match() and fmt in style.keys():
            cpf_strfmt = style[fmt]
        return cpf_strfmt

    def digits_match(self):
        B = False
        if self.pattern_match():
            cpf = self.strfmt("raw")
            cpf_black_list = ["00000000000", "00000000191"]
            if cpf not in cpf_black_list:
                D = [0, 0]
                for i in range(9):
                    D[0] += (10 - i) * int(cpf[i])
                for i in range(10):
                    D[1] += (11 - i) * int(cpf[i])
                D0_is_OK = ((10 * D[0]) % 11) % 10 == int(cpf[9])
                D1_is_OK = ((10 * D[1]) % 11) % 10 == int(cpf[10])
                if D0_is_OK and D1_is_OK:
                    B = True
        return B

    def __repr__(self):
        return self.strfmt("fmt")


class DATE:
    re_d = r"0[1-9]|[12][0-9]|3[01]"
    re_m = r"0[1-9]|1[012]"
    re_y = r"[0-9]{4}"

    dt_1 = re.compile(r"(%s)[/-]?(%s)[/-]?(%s)" % (re_y, re_m, re_d))
    dt_2 = re.compile(r"(%s)[/-]?(%s)[/-]?(%s)" % (re_d, re_m, re_y))

    def __init__(self, datestr):
        self.datestr = datestr

    def patterns_match(self):
        B = False
        if self.dt_1.match(self.datestr) or self.dt_2.match(self.datestr):
            B = True
        return B

    def dissect(self):
        DISSECT = None
        if self.patterns_match():
            if self.dt_1.match(self.datestr):
                Y = self.dt_1.match(self.datestr).group(1)
                M = self.dt_1.match(self.datestr).group(2)
                D = self.dt_1.match(self.datestr).group(3)
            else:
                Y = self.dt_2.match(self.datestr).group(3)
                M = self.dt_2.match(self.datestr).group(2)
                D = self.dt_2.match(self.datestr).group(1)
            DISSECT = Y, M, D
        return DISSECT

    def exists(self):
        B = False
        if self.patterns_match():
            Y, M, D = self.dissect()
            y, m, d = int(Y), int(M), int(D)
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
            is_leap_year = False
            if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0):
                is_leap_year = True
            if is_leap_year and (m == 2):
                ndays[m] += 1
            if d <= ndays[m]:
                B = True
        return B

    def isofmt(self):
        isoformat = None
        if self.exists():
            Y, M, D = self.dissect()
            isoformat = f"{Y}{M}{D}"
        return isoformat

    def dateobj(self):
        dobj = None
        if self.exists():
            dobj = datetime.fromisoformat(self.isofmt())
        return dobj

    def strfmt(self, fmt):
        strfmt = None
        if self.exists():
            style = {
                "yyyy-mm-dd": "%Y-%m-%d",
                "yyyy/mm/dd": "%Y/%m/%d",
                "dd-mm-yyyy": "%d-%m-%Y",
                "dd/mm/yyyy": "%d/%m/%Y",
            }
            strfmt = self.dateobj().strftime(style[fmt])
        return strfmt

    def is_not_in_the_future(self):
        B = False
        if self.exists():
            if self.dateobj() <= datetime.now():
                B = True
        return B

    def year_belongs_to_selected_range(self):
        B = False
        if self.exists():
            if self.dateobj().year in range(1995, 2020):
                B = True
        return B

    def __repr__(self):
        return self.isofmt()


def beancount(dt1, dt2):
    if dt1 < dt2:
        beans = f"{(dt2 - dt1).days} dias"
    else:
        beans = "---"
    return beans


save_the_date = {
    "registration": {
        "opening": DATE("20240615"),
        "closing": DATE("20240715"),
    },
    "step": {
        "1": DATE("20240914"),
        "2": DATE("20241005"),
    },
}


payload = {
    "edition": 2024,
    "quota": 10,
    "save_the_date": save_the_date,
    "days_until": {
        "registration": {
            "opening": beancount(
                datetime.today(),
                save_the_date["registration"]["opening"].dateobj(),
            ),
            "closing": beancount(
                datetime.today(),
                save_the_date["registration"]["closing"].dateobj(),
            ),
        },
        "step": {
            "1": beancount(
                datetime.today(), save_the_date["step"]["1"].dateobj()
            ),
            "2": beancount(
                datetime.today(), save_the_date["step"]["2"].dateobj()
            ),
        },
    },
}
