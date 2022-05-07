SHELL := /bin/bash
CWD := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
ME := $(shell whoami)

nothing:
	@echo "do nothing"

up:
	docker build . -t harelab_bot:3.0.0
	docker run -it -d --name hare_lab_bot -v data:/usr/src/bot/bot/data harelab_bot:3.0.0

migration:
	python data_base_migration.py