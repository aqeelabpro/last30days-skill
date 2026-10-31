# Cursor Cloud image for last30days research.
# Ubuntu 24.04, Python 3.12 from apt, Node.js 22 from the official tarball.
# The builder stage is the only place that downloads a file, and it checks
# the published SHA-256 before extracting. Nothing is piped into a shell.
# The runtime image has no curl, no OpenSSH client, no Docker client, and no
# browser. It runs as the existing ubuntu user.

FROM ubuntu:24.04 AS node

ARG NODE_VERSION=22.23.4
# From https://nodejs.org/dist/v22.23.4/SHASUMS256.txt (linux-x64 tarball).
ARG NODE_SHA256=1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/node.tar.xz \
        "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
    && echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c - \
    && mkdir -p /opt/node \
    && tar -xJf /tmp/node.tar.xz -C /opt/node --strip-components=1 \
    && rm /tmp/node.tar.xz

FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates python3 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 --version

COPY --from=node /opt/node /usr/local

# Process environment wins over ~/.config/last30days/.env. These locks stay
# on even if a later command forgets a flag. Polymarket research is excluded.
# doctor, invoked directly, still probes gamma-api.polymarket.com; use
# .cursor/research.sh, which refuses that command.
ENV FROM_BROWSER=off \
    BROWSER_CONSENT=false \
    AGENTCOOKIE=off \
    LAST30DAYS_SKIP_KEYCHAIN=1 \
    LAST30DAYS_TRUSTPILOT_NO_BROWSER=1 \
    LAST30DAYS_NATIVE_SEARCH=1 \
    EXCLUDE_SOURCES=polymarket \
    LAST30DAYS_MEMORY_DIR=/workspace/.last30days-out \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /workspace/.last30days-out \
    && chown -R ubuntu:ubuntu /workspace \
    && node --version \
    && npm --version

USER ubuntu
WORKDIR /workspace
