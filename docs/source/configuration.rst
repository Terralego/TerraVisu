=============
Configuration
=============

---------------------
Environment variables
---------------------

Add your environment variables in app.env file.

^^^^^^^
General
^^^^^^^

.. envvar:: ALLOWED_HOSTS

    domains allowed to be used by your instance. Support comma separated values.

    Example::

        ALLOWED_HOSTS=mysite.fr  # ALLOWED_HOSTS=mysite.fr,my.other.site.fr


.. envvar:: SECRET_KEY

    unique secret key for your instance. (https://djecrety.ir/)

    Example::

        SECRET_KEY=zbesj@t3_&u75&l=xk@ftg1yh4wy)i)9!z+(v$ig7*-*lkd6om


.. envvar:: SSL_ENABLED

    Set true if your site is behind ssl proxy.

    Example::

        SSL_ENABLED=True

    Default::

        False


^^^^^^^^^^^^
OIDC Connect
^^^^^^^^^^^^

To allow OIDC login, you should configure these settings.

.. envvar:: OIDC_ENABLE_LOGIN

    Enable OIDC connect login.

    Example::

        OIDC_ENABLE_LOGIN=True

    Default::

        False

.. envvar:: OIDC_DISABLE_INTERNAL_LOGIN

    Disable internal login if OIDC enabled. (direct redirection to OIDC login)

    Example::

        OIDC_DISABLE_INTERNAL_LOGIN=True

    Default::

        False

.. envvar:: OIDC_AUTH_SERVER

    Set your OIDC Realm URL.

    Example::

        OIDC_AUTH_SERVER=https://your.openid.com/realms/master

.. envvar:: OIDC_AUTH_CLIENT_ID

    Set your OIDC Client ID.

    Example::

        OIDC_AUTH_CLIENT_ID=your-client-id

.. envvar:: OIDC_AUTH_CLIENT_SECRET

    Set your OIDC Client secret.

    Example::

        OIDC_AUTH_CLIENT_SECRET=7GcKm7XiWIE6BRscGHZZku

.. envvar:: OIDC_AUTH_SCOPE

    Set your OIDC Client scope. Support comma separated values.

    Example::

        OIDC_AUTH_SCOPE=openid,email

    Default::

        openid
