Visu - Front

## Install

    npm ci
    cp public/env.dist.json public/env.json
    cp public/settings.dist.json public/settings.json

You may have to change some data in your personnal env.json and settings.json files.

## Start

    npm start

## Build

    npm run build

## Tests

    npm test

## To execute e2e tests

To run the pipeline locally, you need to install the last version of [gitlab runner](https://docs.gitlab.com/runner/install/) then execute:

    gitlab-runner exec docker --docker-privileged --env REGISTRY_USER=<registry_user> --env REGISTRY_PASSWD="<registry_password>" --env PYFILES_REGION_NAME=<region> --env PYFILES_ENDPOINT_URL=<endpoint_url> --env PYFILES_SECRET_KEY=<secret_key> --env PYFILES_BUCKET_NAME=<user> --env PYFILES_ACCESS_KEY=<access_key> --env MAPBOX_ACCESS_TOKEN=<access_token> --env DOCKER_TLS_CERTDIR="" --timeout 3600 cypress

Dont forget to replace each env var with correct value.
