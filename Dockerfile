# Stage 1: Build
FROM node:20-alpine AS build
RUN apk update && apk upgrade --no-cache
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Production — uses nginxinc/nginx-unprivileged which runs as non-root (UID 101)
FROM nginxinc/nginx-unprivileged:stable-alpine AS prod
USER root
RUN apk update && apk upgrade --no-cache
USER 101

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

USER 101
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:8080/health || exit 1
