APP_NAME := open2300
APP_USER := weather
APP_GROUP := weather
INSTALL_DIR := /opt/$(APP_NAME)
SYSTEMD_DIR := /etc/systemd/system
SERVICE_NAME := $(APP_NAME)-python
SERVICE_FILE := systemd/$(SERVICE_NAME).service
TIMER_FILE := systemd/$(SERVICE_NAME).timer
REQUIREMENTS ?= requirements.txt
PYTHON ?= python3
SUDO ?= sudo
SERIAL_GROUP := dialout

.PHONY: help install install-rpi install-user install-service enable restart disable

help:
	@printf '%s\n' \
		'make install       Install Python open2300 under /opt/open2300' \
		'make install-rpi   Install using Raspberry Pi requirements' \
		'make enable        Enable and start the systemd timer' \
		'make restart       Restart the timer' \
		'make disable       Stop and disable the timer'

install: install-user
	$(SUDO) install -d -o root -g $(APP_GROUP) -m 0750 $(INSTALL_DIR)
	$(SUDO) $(PYTHON) -m venv $(INSTALL_DIR)/.venv
	$(SUDO) $(INSTALL_DIR)/.venv/bin/python -m pip install --upgrade pip
	$(SUDO) $(INSTALL_DIR)/.venv/bin/pip install -r $(REQUIREMENTS)
	$(SUDO) $(INSTALL_DIR)/.venv/bin/pip install --no-deps .
	$(SUDO) install -o root -g $(APP_GROUP) -m 0640 open2300-dist.conf $(INSTALL_DIR)/open2300-dist.conf
	@if ! $(SUDO) test -e $(INSTALL_DIR)/open2300.conf; then \
		$(SUDO) install -o root -g $(APP_GROUP) -m 0640 open2300-dist.conf $(INSTALL_DIR)/open2300.conf; \
		printf '%s\n' 'Created $(INSTALL_DIR)/open2300.conf from the example; edit serial, PostgreSQL, and MQTT settings.'; \
	fi
	$(MAKE) install-service

install-rpi:
	$(MAKE) install REQUIREMENTS=requirements-rpi.txt

install-user:
	@if ! getent group $(APP_GROUP) >/dev/null; then \
		$(SUDO) groupadd --system $(APP_GROUP); \
	fi
	@if ! getent passwd $(APP_USER) >/dev/null; then \
		$(SUDO) useradd --system --gid $(APP_GROUP) --home-dir $(INSTALL_DIR) --shell /usr/sbin/nologin $(APP_USER); \
	fi
	@if ! getent group $(SERIAL_GROUP) >/dev/null; then \
		printf '%s\n' 'Required serial group $(SERIAL_GROUP) does not exist.' >&2; \
		exit 1; \
	fi
	$(SUDO) usermod --append --groups $(SERIAL_GROUP) $(APP_USER)

install-service:
	$(SUDO) install -o root -g root -m 0644 $(SERVICE_FILE) $(SYSTEMD_DIR)/$(SERVICE_NAME).service
	$(SUDO) install -o root -g root -m 0644 $(TIMER_FILE) $(SYSTEMD_DIR)/$(SERVICE_NAME).timer
	$(SUDO) systemctl daemon-reload

enable:
	$(SUDO) systemctl enable --now $(SERVICE_NAME).timer

restart:
	$(SUDO) systemctl restart $(SERVICE_NAME).timer

disable:
	$(SUDO) systemctl disable --now $(SERVICE_NAME).timer
