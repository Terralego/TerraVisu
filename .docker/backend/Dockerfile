FROM ubuntu:jammy as base

ENV PYTHONBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV TZ UTC
ENV POSTGRES_HOST db
ENV POSTGRES_PORT 5432

RUN apt-get -y -qq update \
    && apt-get -y -qq install \
    python3 \
    libpq5 \
    binutils \
    libproj-dev \
    gdal-bin \
    gettext \
    postgresql-client \
    tzdata \
    netcat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

RUN adduser docker --disabled-password
RUN mkdir -p /opt/terra-visu && chown docker:docker /opt
WORKDIR /opt/terra-visu

COPY .docker/backend/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000

FROM base as build

RUN apt-get -y -qq update \
    && apt-get -y -qq install \
    python3-dev \
    python3-venv \
    build-essential \
    libpq-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

USER docker

RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir --upgrade pip wheel

COPY requirements.txt /opt/terra-visu/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade -r /opt/terra-visu/requirements.txt

FROM build as dev

COPY dev-requirements.txt /opt/terra-visu/dev-requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade -r /opt/terra-visu/dev-requirements.txt
COPY .docker/backend/update.sh /usr/local/bin/update.sh

CMD /opt/venv/bin/python manage.py runserver 0.0.0.0:8000

FROM base as prod

COPY --from=build /opt/venv /opt/venv

COPY public/admin /opt/admin
COPY project /opt/terra-visu/project
COPY manage.py /opt/terra-visu/manage.py
COPY Procfile /opt/terra-visu/Procfile
COPY .docker/backend/update.sh /usr/local/bin/update.sh

RUN DJANGO_SETTINGS_MODULE=project.settings.tests /opt/venv/bin/python manage.py compilemessages

USER root

RUN apt-get -y -qq update \
    && apt-get -y -qq full-upgrade \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

USER docker

CMD /opt/venv/bin/gunicorn project.wsgi:application --bind 0.0.0.0:8000