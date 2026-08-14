#!/usr/bin/env bash
# ==============================================================================
# Script: stop-app.sh
# Purpose: Stop all active service containers without removing data/volumes.
# Course: CCS3308 - Virtualization and Containers (Assignment 1)
# ==============================================================================

set -e

echo "Stopping app ..."

DB_CONTAINER="taskmanager-db"
WEB_CONTAINER="taskmanager-web"

# Stop web container if running
if docker ps --format '{{.Names}}' | grep -wq "^${WEB_CONTAINER}$"; then
    echo "Stopping container: ${WEB_CONTAINER}..."
    docker stop "${WEB_CONTAINER}" > /dev/null
fi

# Stop database container if running
if docker ps --format '{{.Names}}' | grep -wq "^${DB_CONTAINER}$"; then
    echo "Stopping container: ${DB_CONTAINER}..."
    docker stop "${DB_CONTAINER}" > /dev/null
fi

echo "Application stopped successfully. Persistent volume state is preserved."
