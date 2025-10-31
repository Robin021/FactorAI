# Multi-stage build for production frontend
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (include devDependencies for build: tsc/vite)
RUN npm ci

# Copy source code
COPY . .

# Set build-time environment variables
ARG NODE_ENV=production
ARG VITE_ENABLE_DEV_LOGIN=false
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_AUTHING_APP_ID
ARG VITE_AUTHING_APP_HOST
ARG VITE_AUTHING_REDIRECT_URI

ENV NODE_ENV=$NODE_ENV
ENV VITE_ENABLE_DEV_LOGIN=$VITE_ENABLE_DEV_LOGIN
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_AUTHING_APP_ID=$VITE_AUTHING_APP_ID
ENV VITE_AUTHING_APP_HOST=$VITE_AUTHING_APP_HOST
ENV VITE_AUTHING_REDIRECT_URI=$VITE_AUTHING_REDIRECT_URI

# Build application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# nginx:alpine 已包含 nginx 用户与组，无需重复创建

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]