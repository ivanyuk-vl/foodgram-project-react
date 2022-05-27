# build env
FROM node:13.12.0-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
COPY ./docs/ ./
CMD rm -rf result_build/* result_docs/* && cp -r build/* result_build && cp -r docs/* result_docs
