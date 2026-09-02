FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve the static build behind nginx, which also reverse-proxies /api to
# the backend container. A plain static file server (e.g. `serve`) cannot
# do this, and the app's API client calls relative paths like `/api/...`
# (see src/lib/api.ts) so without this proxy every API call 404s in the
# production/Docker build even though `npm run dev` works fine (Vite's
# own dev-server proxy, see vite.config.ts, only applies to `vite dev`).
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
