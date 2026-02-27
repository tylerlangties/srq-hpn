# Production Dockerfile for Next.js frontend
# Multi-stage build for optimized image size

FROM node:22-alpine AS base
RUN corepack enable && corepack prepare pnpm@10.27.0 --activate

# Stage 1: Install dependencies
FROM base AS deps
WORKDIR /app

# Copy workspace config files
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json ./apps/web/

# Install dependencies
RUN pnpm install --frozen-lockfile --filter web

# Stage 2: Build the application
FROM base AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules

# Copy source code
COPY apps/web ./apps/web
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ARG NEXT_PUBLIC_POSTHOG_KEY
ARG NEXT_PUBLIC_POSTHOG_HOST
ARG NEXT_PUBLIC_ANALYTICS_DEBUG
ENV NEXT_PUBLIC_POSTHOG_KEY=$NEXT_PUBLIC_POSTHOG_KEY
ENV NEXT_PUBLIC_POSTHOG_HOST=$NEXT_PUBLIC_POSTHOG_HOST
ENV NEXT_PUBLIC_ANALYTICS_DEBUG=$NEXT_PUBLIC_ANALYTICS_DEBUG

# Build the application
WORKDIR /app/apps/web
RUN pnpm build

# Stage 3: Production runner
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy standalone build output
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

# Copy content directory for articles
COPY --from=builder /app/apps/web/content ./apps/web/content

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# The standalone output creates server.js at apps/web/server.js
CMD ["node", "apps/web/server.js"]
