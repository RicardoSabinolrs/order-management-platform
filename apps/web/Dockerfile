# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------------------
# Estagio 1: build do bundle
# ---------------------------------------------------------------------------
FROM node:24-bookworm-slim AS builder

ENV PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /repo

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile --filter @oms/web...

COPY apps/web apps/web
RUN pnpm --filter @oms/web build

# ---------------------------------------------------------------------------
# Estagio 2: nginx servindo estaticos
# ---------------------------------------------------------------------------
FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime

COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /repo/apps/web/dist /usr/share/nginx/html

EXPOSE 8080
