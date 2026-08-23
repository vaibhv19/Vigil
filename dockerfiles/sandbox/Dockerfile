FROM python:3.12-alpine

# Install bash, curl, shadow (for useradd/groupadd)
RUN apk add --no-cache bash curl shadow

# Create non-root user with UID 1000
RUN groupadd -g 1000 vigil-user && \
    useradd -u 1000 -g vigil-user -m -s /bin/bash vigil-user

# Prepare the workspace directory
RUN mkdir -p /workspace && chown -R vigil-user:vigil-user /workspace

# Run as non-root user by default
USER vigil-user
WORKDIR /workspace
