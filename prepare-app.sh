#!/usr/bin/env bash
# ==============================================================================
# Script: prepare-app.sh
# Purpose: Prepare Docker network, persistent volume, and build custom image.
# Course: CCS3308 - Virtualization and Containers (Assignment 1)
# ==============================================================================

set -e

echo "Preparing app ..."

# Define resource names
NETWORK_NAME="taskmanager-net"
VOLUME_NAME="taskmanager_pgdata"
IMAGE_NAME="taskmanager-web:latest"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/app" && pwd)"

# 1. Create Docker isolated bridge network if it doesn't already exist
if ! docker network ls --format '{{.Name}}' | grep -wq "^${NETWORK_NAME}$"; then
    echo "Creating Docker network: ${NETWORK_NAME}..."
    docker network create "${NETWORK_NAME}"
else
    echo "Docker network '${NETWORK_NAME}' already exists."
fi

# 2. Create Docker named persistent volume if it doesn't already exist
if ! docker volume ls --format '{{.Name}}' | grep -wq "^${VOLUME_NAME}$"; then
    echo "Creating persistent named volume: ${VOLUME_NAME}..."
    docker volume create "${VOLUME_NAME}"
else
    echo "Docker volume '${VOLUME_NAME}' already exists."
fi

# 3. Pull base image for database service
echo "Pulling PostgreSQL 16 Alpine base image..."
docker pull postgres:16-alpine

# 4. Build custom Docker image for the web application
echo "Building custom Docker image: ${IMAGE_NAME}..."
docker build -t "${IMAGE_NAME}" "${APP_DIR}"

echo "Application resources prepared successfully."
