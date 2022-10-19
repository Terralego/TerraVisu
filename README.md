TerraVisu
=========

Development
-----------

### Requirements

* docker & compose
* NVM for frontend development

### Start

1. Prepare stack
```bash
    cp db.env.dist db.env
    docker-compose up
```
2. Create your super user
```bash
    docker-compose run --rm web ./manage.py createsuperuser
```
### Frontend development & testing

```bash
    nvm use
    # nvm install if required
    npm ci
    npm run dev
```

  * Source files are located in project/frontend/src directory.
  * Webpack watch files in dev mode.
  * Compiled files are located in project/frontend/static directory. Don't commit them.

And go to ``http://localhost:8000``

### Backend development and testing

Production
----------

    npm run build