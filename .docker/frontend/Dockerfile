ARG NODE_VERSION=18

FROM node:${NODE_VERSION}-alpine

WORKDIR /app

COPY package.json ./
COPY package-lock.json ./

RUN npm ci

CMD ["npm", "run", "dev"]