# React app for production: build with Vite, then serve the static files.
# Vite reads frontend/.env at build time (Supabase URL and publishable key; no
# secrets). VITE_API_URL defaults to "" so API calls go to /api/... on the same
# origin, which deploy/Caddyfile routes to the api service.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# A real environment variable overrides the value in frontend/.env.
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM caddy:2-alpine
COPY docker/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
EXPOSE 80
