===========
Development
===========

-------------
Prepare stack
-------------

:
    cp db.env.dist db.env
    cp app.env.dist app.env
    docker-compose build

-------------
Init database
-------------

:
    docker-compose run --rm web ./manage.py createsuperuser


---------------------
Create your superuser
---------------------

:
    docker-compose run --rm web ./manage.py createsuperuser


---------------
Launch stack
---------------

:
    docker-compose up


Then got to http://127.0.0.1:8000