#!/usr/bin/env bash
# ==============================================================================
# Script: remove-app.sh
# Purpose: Cleanly remove all resources (containers, network, volume, and images).
# Course: CCS3308 - Virtualization and Containers (Assignment 1)
# ==============================================================================

set -e

# Stop and remove containers
DB_CONTAINER="taskmanager-db"
WEB_CONTAINER="taskmanager-web"
NETWORK_NAME="taskmanager-net"
VOLUME_NAME="taskmanager_pgdata"
IMAGE_NAME="taskmanager-web:latest"

if docker ps -a --format '{{.Names}}' | grep -wq "^${WEB_CONTAINER}$"; then
    echo "Removing container: ${WEB_CONTAINER}..."
    docker rm -f "${WEB_CONTAINER}" > /dev/null 2>&1 || true
fi

if docker ps -a --format '{{.Names}}' | grep -wq "^${DB_CONTAINER}$"; then
    echo "Removing container: ${DB_CONTAINER}..."
    docker rm -f "${DB_CONTAINER}" > /dev/null 2>&1 || true
fi

# Remove network
if docker network ls --format '{{.Name}}' | grep -wq "^${NETWORK_NAME}$"; then
    echo "Removing network: ${NETWORK_NAME}..."
    docker network rm "${NETWORK_NAME}" > /dev/null 2>&1 || true
fi

# Remove persistent named volume
if docker volume ls --format '{{.Name}}' | grep -wq "^${VOLUME_NAME}$"; then
    echo "Removing volume: ${VOLUME_NAME}..."
    docker volume rm "${VOLUME_NAME}" > /dev/null 2>&1 || true
fi

# Remove custom image
if docker images --format '{{.Repository}}:{{.Tag}}' | grep -wq "^${IMAGE_NAME}$"; then
    echo "Removing custom image: ${IMAGE_NAME}..."
    docker rmi "${IMAGE_NAME}" > /dev/null 2>&1 || true
fi

# Assignment-specified workflow output
echo "Removed app."
