import re

payload = {
    "edition": 2024,
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
