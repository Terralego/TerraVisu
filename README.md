TerraVisu
=========

Development
-----------

### Requirements

* docker & compose
* NVM for frontend development

### Start

```bash
    cp db.env.dist db.env
    docker-compose up
```
### Frontend development

```bash
    nvm use
    # nvm install if required
    npm ci
    npm run dev
```

  * Source files are located in project/frontend/src directory.
  * Webpack watch files in dev mode.
  * Compiled files are located in project/frontend/static directory. Don't commit them.

Production
----------

    npm run build