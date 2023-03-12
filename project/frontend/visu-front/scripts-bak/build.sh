#!/bin/sh
cp _headers ./build
cat _redirects | sed s/ADMIN_HOST/$ADMIN_HOST/ | sed s/BACKEND_URL/$BACKEND_URL/ > ./build/_redirects
