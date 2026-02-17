VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: run install

run: $(VENV)/.installed
	$(PYTHON) main.py

install: $(VENV)/.installed

$(VENV)/.installed: requirements.txt
	$(PIP) install -r requirements.txt
	touch $@

requirements.txt:
	@echo "openpyxl\nrequests" > $@
