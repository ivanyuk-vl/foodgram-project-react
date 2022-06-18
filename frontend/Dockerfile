# build env
FROM node:13.12.0-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
CMD rm -rf result_build/* && cp -r build/* result_build && mkdir result_build/api && cp -r docs result_build/api
