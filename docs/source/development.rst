===========
Development
===========

-------------
Prepare stack
-------------

..  code-block:: bash

    cp db.env.dist db.env
    cp app.env.dist app.env
    docker compose build

-------------
Init database
-------------

..  code-block:: bash

    docker compose run --rm web ./manage.py migrate


-----------------
Load initial data
-----------------

..  code-block:: bash

    docker compose run --rm web ./manage.py loaddata project/fixtures/initial.json


---------------------
Create your superuser
---------------------

..  code-block:: bash

    docker compose run --rm web ./manage.py createsuperuser

-------------------------
Prepare admin if required
-------------------------

..  code-block:: bash

    make build_admin


----------------------------
Prepare frontend if required
----------------------------

..  code-block:: bash

    make build_front


------------
Launch stack
------------

..  code-block:: bash

    docker compose up


------
Access
------

Frontend
--------

http://visu.localhost:8080


Admin
-----

http://visu.localhost:8080/admin/

Django admin (config / debug)
-----------------------------

http://visu.localhost:8080/config/


-------
Linting
-------

We use flake8, isort and black rules. You can run :

..  code-block:: bash

    make lint


to check them