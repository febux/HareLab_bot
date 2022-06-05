SHELL := /bin/bash
CWD := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
ME := $(shell whoami)

nothing:
	@echo "do nothing"

build:
	docker build . -t harelab_bot:test

run:
	docker run -it -d --restart on-failure:3 --name hare_lab_bot -v data:/usr/src/bot/bot/data harelab_bot:test

up:
	docker build . -t harelab_bot:test
	docker run -it -d --restart on-failure:3 --name hare_lab_bot -v data:/usr/src/bot/bot/data harelab_bot:test

migration:
	python db_migration__new.py

save:
	docker save -o D://image.tar harelab_bot
