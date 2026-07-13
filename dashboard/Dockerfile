# ─── Build-Stage: Vue-App bauen ───────────────────────────────────────────────
FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# API-Basis-URL wird zur Build-Zeit ins Bundle eingebacken (Browser ruft das Backend
# über den vom Host veröffentlichten Port auf).
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# ─── Serve-Stage: statisch via nginx ──────────────────────────────────────────
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
