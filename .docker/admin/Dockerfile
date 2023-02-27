ARG NODE_VERSION=12

FROM node:${NODE_VERSION}

WORKDIR /app

COPY ./admin/package.json ./
COPY ./admin/package-lock.json ./

RUN npm ci

CMD ["npm", "run", "start"]