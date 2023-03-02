Requirements
============

* You need docker installed. Compose plugin is recommended in the configuration below.
    See `Docker <https://docs.docker.com/engine/install/>`_.

* **Optional** : if you want to use external database, prepare a postgresql 11+ (15 recommended) postgis2.5 (3.3 recommended) database with postgis enabled, and a dedicated user.

    You can use external database by commenting postgres container and volume references in docker-compose.yml, and set variables in your conf/visu.env file :
        * POSTGRES_HOST
        * POSTGRES_PORT
        * POSTGRES_USER
        * POSTGRES_PASSWORD
        * POSTGRES_DB

Add local IPs in `pg_hba.conf` to allow connection from docker containers to your database.

* You can use external nginx proxy. Edit provided nginx conf file and comment nginx references in docker-compose.yml. Fix web:8000 to 127.0.0.1:8000 in nginx.conf.


Install
=======

* Download `zip package <https://github.com/submarcos/TerraVisu/releases/latest/download/install.zip>`_

* Unzip it where you want

  .. code-block :: bash

      unzip install.zip
      cd terra_visu


* Prepare environment variables

  .. code-block :: bash

      ./conf/visu.env

  **-> Set or change all required values**

at least:

        * ALLOWED_HOST       # list of your final host(s), comma separated values
        * SECRET_KEY         # unique key for your project. See https://djecrety.ir/
        * POSTGRES_USER      # a dedicated user for your database
        * POSTGRES_PASSWORD  # a dedicated password for your database


* Pull images

  .. code-block :: bash

      docker compose pull


* Init database and project config

  .. code-block :: bash

      docker compose run --rm web update.sh

* Create your super user

  .. code-block :: bash

      docker compose run --rm web ./manage.py createsuperuser

* Load initial data

  .. code-block :: bash

      docker compose run --rm web ./manage.py loaddata project/fixtures/initial.json


* Launch stack

  .. code-block :: bash

      docker compose up -d

* ... and access to your project

  .. code-block :: bash

      http://<your_domain>/


Update
======

* Read `release notes <https://github.com/submarcos/TerraVisu/releases>`_ about bugfix, news and breaking changes.

* Backup your data (database, public/media and var/ folder)

* Pull latest image

  .. code-block :: bash

      docker compose pull


* Run post update script

  .. code-block :: bash

      docker compose run --rm web update.sh


* Relaunch your stack

  .. code-block :: bash

      docker compose down
      docker compose up -d






cp .env.dist .env

FILL database informations

FILL ALLOWED_HOSTS matching your domain

docker compose run --rm web update.sh
docker compose run --rm web ./manage.py loaddata project/fixtures/initial.json
docker compose run --rm web ./manage.py createsuperuser

then login with it