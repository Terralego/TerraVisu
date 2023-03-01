#!/usr/bin/make

SHELL = /bin/sh

CURRENT_UID := $(shell id -u)
CURRENT_UID := $(shell id -g)

export CURRENT_UID
export CURRENT_GID

build_admin:
	rm -rf ./public/admin
	git submodule update --init
	git submodule update --remote
	docker compose -f .docker/admin/docker-compose.yml pull
	docker compose -f .docker/admin/docker-compose.yml run --rm admin bash -c "npm ci --legacy-peer-deps && npx react-scripts --openssl-legacy-provider build"
	mv ./admin/build ./public/admin
	rm -rf ./admin/node_modules

build_prod: build_admin
	docker pull ubuntu:jammy
	docker build -t terra-visu:latest -f .docker/backend/Dockerfile .

messages:
	docker compose run --rm web ./manage.py makemessages -a --no-location --no-obsolete
	docker compose run --rm web ./manage.py compilemessages

tests:
	docker compose run --rm web ./manage.py test -v 3 --settings=project.settings.tests

coverage:
	docker compose run --rm web coverage run ./manage.py test -v 3 --settings=project.settings.tests
	docker compose run --rm web coverage report -m

sphinx:
	docker compose run --workdir=/opt/terra-visu/docs --rm web make html -e SPHINXOPTS="-W"

black:
	docker compose run --rm web black project

isort:
	docker compose run --rm web isort project

flake8:
	docker compose run --rm web flake8 project

lint: black isort flake8