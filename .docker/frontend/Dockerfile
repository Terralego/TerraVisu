ARG NODE_VERSION=12

FROM --platform=linux/amd64 node:${NODE_VERSION}

RUN ls -al

WORKDIR /app/project/frontend/visu-front/

COPY ./project/frontend/visu-front/package.json ./
COPY ./project/frontend/visu-front/package-lock.json ./

RUN npm ci

CMD ["npm", "run", "build-watch"]
