VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: run install test

run: $(VENV)/.installed
	$(PYTHON) main.py

install: $(VENV)/.installed

test: $(VENV)/.installed
	$(VENV)/bin/pytest tests/ -v

$(VENV)/.installed: requirements.txt
	$(PIP) install -r requirements.txt
	touch $@

requirements.txt:
	@echo "openpyxl\nrequests" > $@
