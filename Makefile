#!/usr/bin/make

SHELL = /bin/sh

CURRENT_UID := $(shell id -u)
CURRENT_GID := $(shell id -g)

export CURRENT_UID
export CURRENT_GID

build_admin:
	rm -rf ./public/admin
	docker compose -f .docker/admin/docker-compose.yml pull
	docker compose -f .docker/admin/docker-compose.yml run --rm admin bash -c "npm ci --legacy-peer-deps && npx react-scripts --openssl-legacy-provider build"
	mv ./admin/build ./public/admin
	rm -rf ./admin/node_modules

build_front:
	docker compose -f .docker/frontend/docker-compose.yml pull
	docker compose -f .docker/frontend/docker-compose.yml run --rm front bash -c "git config --global url.\"https://github.com/\".insteadOf ssh://git@github.com/ && npm ci --production && npm run build"
	find ./public -maxdepth 1 -type f -exec rm {} \;
	if [ -e ./public/static ]; then rm -r ./public/static ./public/images ./public/locales; fi
	mv ./front/build/* ./public/
	rm -rf ./front/node_modules

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

format:
	docker compose run --remove-orphans --no-deps --rm web ruff format project

lint:
	docker compose run --remove-orphans --no-deps --rm web ruff check --fix project

force_lint:
	docker compose run --remove-orphans --no-deps --rm web ruff check --fix --unsafe-fixes project

quality: lint format

deps:
	docker compose run --rm web bash -c "uv pip compile pyproject.toml -o requirements.txt && cd docs && uv pip compile requirements.in -o requirements.txt && cd .. && uv pip compile pyproject.toml --extra dev -c requirements.txt -o requirements-dev.txt"

django:
	docker compose run --rm web ./manage.py $(filter-out $@,$(MAKECMDGOALS))

docs_serve:
	docker compose run -p 8800:8800 -w=/opt/terra-visu/docs --rm web sphinx-autobuild -c source -b html --host 0.0.0.0 --port 8800 ./source ./build/html

docs_build:
	docker compose run -w=/opt/terra-visu/docs --rm web make html