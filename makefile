build:
	gunicorn -b localhost:8000 -w 4 omeg.core:omeg

black:
	isort omeg/auth/emails.py
	isort omeg/auth/forms.py
	isort omeg/auth/routes.py
	isort omeg/conf/boost.py
	isort omeg/conf/setup.py
	isort omeg/core.py
	isort omeg/data/load.py
	isort omeg/home/routes.py
	isort omeg/mold/models.py
	isort omeg/user/emails.py
	isort omeg/user/forms.py
	isort omeg/user/routes.py
	black -l 79 omeg/auth/emails.py
	black -l 79 omeg/auth/forms.py
	black -l 79 omeg/auth/routes.py
	black -l 79 omeg/conf/boost.py
	black -l 79 omeg/conf/setup.py
	black -l 79 omeg/core.py
	black -l 79 omeg/data/load.py
	black -l 79 omeg/home/routes.py
	black -l 79 omeg/mold/models.py
	black -l 79 omeg/user/emails.py
	black -l 79 omeg/user/forms.py
	black -l 79 omeg/user/routes.py

clean:
	find . -type d -name __pycache__ | xargs rm -rf

ready:
	python3 -m venv venv; \
	. venv/bin/activate; \
	pip install -U pip; \
	pip install -r requirements.txt; \
	deactivate

.PHONY: build black clean ready
