FROM ubuntu:noble AS base

LABEL org.opencontainers.image.authors="Makina Corpus Territoires"
LABEL org.opencontainers.image.source="https://github.com/Terralego/TerraVisu/"
LABEL org.opencontainers.image.documentation="https://terravisu.readthedocs.io/"
LABEL org.opencontainers.image.vendor="Makina Corpus Territoires"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.url="https://territoires.makina-corpus.com/"
LABEL org.opencontainers.image.title="TerraVisu"
LABEL org.opencontainers.image.description="Manage and visualize your geographic data."

ENV PYTHONBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV TZ=UTC
ENV POSTGRES_HOST=db
ENV POSTGRES_PORT=5432
ENV CUSTOM_SETTINGS_FILE="/opt/terra-visu/var/conf/custom.py"

RUN apt-get -y -qq update \
    && apt-get -y -qq install \
    ca-certificates \
    python3 \
    libpq5 \
    binutils \
    libproj-dev \
    gdal-bin \
    gettext \
    postgresql-client \
    tzdata \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

RUN useradd --system docker -u 1001 && mkdir -p /opt/terra-visu && chown docker:docker /opt
WORKDIR /opt/terra-visu

COPY .docker/backend/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000

FROM base AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get -y -qq update && apt-get -y -qq install \
    python3-dev \
    build-essential \
    libpq-dev \
    git

USER docker

ENV UV_CACHE_DIR=/opt/terravisu/var/cache/
RUN uv venv /opt/venv
ENV UV_PYTHON=/opt/venv/bin/python
ENV UV_LINK_MODE=copy

RUN --mount=type=bind,src=./requirements.txt,dst=/requirements.txt \
    --mount=type=cache,target=/opt/geotrek-admin/var/cache/,sharing=locked,uid=1001,gid=1001 \
    uv pip install -r /requirements.txt

FROM build AS dev

RUN --mount=type=bind,src=./requirements-dev.txt,dst=/requirements-dev.txt \
    --mount=type=bind,src=./docs/requirements.txt,dst=/requirements-doc.txt \
    --mount=type=cache,target=/opt/terravisu/var/cache/,sharing=locked,uid=1001,gid=1001 \
    uv pip install -r /requirements-dev.txt -r /requirements-doc.txt

CMD ["/opt/venv/bin/python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prod

ENV GUNICORN_WORKERS=1
ENV GUNICORN_TIMEOUT=60

COPY --from=build /opt/venv /opt/venv

COPY front/build /opt/frontend
COPY admin/build /opt/frontend/admin
COPY project /opt/terra-visu/project
COPY manage.py /opt/terra-visu/manage.py
COPY Procfile /opt/terra-visu/Procfile
COPY .docker/backend/update.sh /usr/local/bin/update.sh

RUN DJANGO_SETTINGS_MODULE=project.settings.tests /opt/venv/bin/python manage.py compilemessages

USER docker

CMD ["/opt/venv/bin/gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "$GUNICORN_WORKERS", "--timeout", "$GUNICORN_TIMEOUT"]