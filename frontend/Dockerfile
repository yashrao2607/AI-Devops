# ==============================================================================
# DeploySafe Frontend Dockerfile (Multi-Stage Production Build)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build the React + Vite static bundle
# ------------------------------------------------------------------------------
FROM node:20-alpine as builder

WORKDIR /app

# Copy dependency specifications first for Docker layer caching
COPY frontend/package.json frontend/package-lock.json* /app/

# Install dependencies cleanly
RUN npm ci

# Copy full frontend source code
COPY frontend/ /app/

# Build production bundle into /app/dist
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Serve with lightweight Nginx Alpine container
# ------------------------------------------------------------------------------
FROM nginx:1.27-alpine as production

# Remove default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration (reverse proxy + SPA routing)
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Healthcheck to verify Nginx availability
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:80/ || exit 1

# Launch Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
