===========
Development
===========

-------------
Prepare stack
-------------

..  code-block:: bash

    cp db.env.dist db.env
    cp app.env.dist app.env
    docker-compose build

-------------
Init database
-------------

..  code-block:: bash

    docker-compose run --rm web ./manage.py migrate


---------------------
Create your superuser
---------------------

..  code-block:: bash

    docker-compose run --rm web ./manage.py createsuperuser


---------------
Launch stack
---------------

..  code-block:: bash

    docker-compose up


Then go to http://127.0.0.1:8000