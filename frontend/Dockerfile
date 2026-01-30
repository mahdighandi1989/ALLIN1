FROM node:20-alpine AS builder

# Create app directory and user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

WORKDIR /app

# Copy package files with proper ownership
COPY --chown=nextjs:nodejs package*.json ./

# Switch to non-root user for build
USER nextjs

# Install dependencies
RUN npm ci --only=production

# Copy source code with proper ownership
COPY --chown=nextjs:nodejs . .

# Build the application
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy built application with proper ownership
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json

# Create necessary directories with proper ownership
RUN mkdir -p /app/.next/cache && chown -R nextjs:nodejs /app/.next/cache
RUN mkdir -p /tmp && chmod 1777 /tmp

# Switch to non-root user before running the application
USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })" || exit 1

CMD ["node", "server.js"]