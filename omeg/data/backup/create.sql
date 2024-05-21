CREATE TABLE IF NOT EXISTS school(
  inep CHAR(8) NOT NULL,
  name CHAR(96) NOT NULL,
  city CHAR(27) NOT NULL,
  zone CHAR(6) NOT NULL,
  tier CHAR(7) NOT NULL,
  code CHAR(9) NOT NULL,
  pnum CHAR(14) NOT NULL,
  latd FLOAT,
  lotd FLOAT,
  PRIMARY KEY (inep)
);

CREATE TABLE IF NOT EXISTS professor(
  taxnr CHAR(11) NOT NULL,
  fname VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  paswd VARCHAR(255) NOT NULL,
  PRIMARY KEY(taxnr)
);

CREATE TABLE IF NOT EXISTS student(
  cpfnr CHAR(11) NOT NULL,
  fname VARCHAR(255) NOT NULL,
  birth DATE NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  PRIMARY KEY(cpfnr)
);

CREATE TABLE IF NOT EXISTS enrollment(
  taxnr CHAR(11) NOT NULL,
  cpfnr CHAR(11) NOT NULL,
  inep CHAR(8) NOT NULL,
  year INT NOT NULL DEFAULT YEAR(CURDATE()),
  role INT NOT NULL,
  gift CHAR NOT NULL DEFAULT 'N',
  CONSTRAINT CHECK (role IN (1, 2, 3)),
  CONSTRAINT CHECK (gift IN ('Ouro', 'Prata', 'Bronze', 'Menção Honrosa', 'Nada')),
  FOREIGN KEY (taxnr) REFERENCES professor (taxnr),
  FOREIGN KEY (cpfnr) REFERENCES student (cpfnr),
  FOREIGN KEY (inep) REFERENCES school (inep),
  PRIMARY KEY (taxnr, cpfnr, inep, year)
);
