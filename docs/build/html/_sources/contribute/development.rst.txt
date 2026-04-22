===========
Development
===========

-------------
Clone project
-------------

..  code-block:: bash

    git clone --recurse-submodules git@github.com:Terralego/TerraVisu.git

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

------------
Modification
------------

- Each modification should be done in a Pull request correctly named and labeled (dependencies, bug, enhancement, ...) with a changelog entry.

---------------
Release process
---------------

- Changelog should be up to date
- assign version number in project/VERSION and docs/source/changelog.rst with date (version in the form YYYY.MM.XX where YYYY is the year, MM the month, XX the release number in the month.)
- Use Release fonction in github to create a release with the same name as the version number
- Use release notes button to generate release notes
- CI publish a new docker image.
- Back to dev by adding "+dev" to project/VERSION and new changelog section with XXXX-XX-XX date and version