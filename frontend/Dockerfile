# Multi-stage build for Next.js static export
# Stage 1: Build the application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install all dependencies (including devDependencies needed for build)
RUN npm ci

# Copy source code
COPY . .

# NEXT_PUBLIC_API_URL must be present AT BUILD TIME (Next.js inlines it into
# the static bundle) — a runtime env var on the nginx container does nothing.
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application (tsc --noEmit && next build → produces out/)
RUN npm run build

# Dev stage (docker-compose.dev.yml targets this): source is bind-mounted and
# `npm run dev` is the compose command — the image just needs node + deps.
FROM builder AS development
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Stage 2: Serve static files with nginx
FROM nginx:alpine AS production

# Copy built static files to nginx html directory
COPY --from=builder /app/out /usr/share/nginx/html

# Copy custom nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
