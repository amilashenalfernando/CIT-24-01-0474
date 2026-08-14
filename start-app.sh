#!/usr/bin/env bash
# ==============================================================================
# Script: start-app.sh
# Purpose: Start and configure all service containers with failure restart policy.
# Course: CCS3308 - Virtualization and Containers (Assignment 1)
# ==============================================================================

set -e

echo "Running app ..."

NETWORK_NAME="taskmanager-net"
VOLUME_NAME="taskmanager_pgdata"
DB_CONTAINER="taskmanager-db"
WEB_CONTAINER="taskmanager-web"
WEB_IMAGE="taskmanager-web:latest"
APP_PORT="${APP_PORT:-5000}"

# Check if default port 5000 is occupied by host OS (e.g. macOS AirPlay Receiver)
# If occupied by a non-docker process, seamlessly use port 5050
if lsof -Pi :${APP_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    # Check if our own web container is already using it
    if ! docker ps --filter "name=^/${WEB_CONTAINER}$" --format '{{.Names}}' | grep -wq "^${WEB_CONTAINER}$"; then
        echo "Notice: Port ${APP_PORT} is occupied by host OS (e.g. macOS AirPlay). Falling back to host port 5050."
        APP_PORT=5050
    fi
fi

# 1. Start or Run Database Container
if docker ps -a --format '{{.Names}}' | grep -wq "^${DB_CONTAINER}$"; then
    if docker ps --format '{{.Names}}' | grep -wq "^${DB_CONTAINER}$"; then
        echo "Database container '${DB_CONTAINER}' is already running."
    else
        echo "Starting existing database container '${DB_CONTAINER}'..."
        docker start "${DB_CONTAINER}" > /dev/null
    fi
else
    echo "Launching new database container '${DB_CONTAINER}'..."
    docker run -d \
        --name "${DB_CONTAINER}" \
        --restart on-failure \
        --network "${NETWORK_NAME}" \
        -v "${VOLUME_NAME}:/var/lib/postgresql/data" \
        -e POSTGRES_DB=taskdb \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgrespassword \
        -p 5432:5432 \
        postgres:16-alpine > /dev/null
fi

# 2. Wait for PostgreSQL readiness
echo "Waiting for PostgreSQL database to be ready..."
for i in {1..20}; do
    if docker exec "${DB_CONTAINER}" pg_isready -U postgres -d taskdb >/dev/null 2>&1; then
        echo "PostgreSQL is ready and accepting connections."
        break
    fi
    sleep 1
done

# 3. Start or Run Web Application Container
if docker ps -a --format '{{.Names}}' | grep -wq "^${WEB_CONTAINER}$"; then
    if docker ps --format '{{.Names}}' | grep -wq "^${WEB_CONTAINER}$"; then
        echo "Web container '${WEB_CONTAINER}' is already running."
    else
        echo "Starting existing web container '${WEB_CONTAINER}'..."
        docker start "${WEB_CONTAINER}" > /dev/null
    fi
else
    echo "Launching new web container '${WEB_CONTAINER}'..."
    docker run -d \
        --name "${WEB_CONTAINER}" \
        --restart on-failure \
        --network "${NETWORK_NAME}" \
        -p "${APP_PORT}:5000" \
        -e DB_HOST="${DB_CONTAINER}" \
        -e DB_PORT=5432 \
        -e DB_NAME=taskdb \
        -e DB_USER=postgres \
        -e DB_PASSWORD=postgrespassword \
        -e APP_PORT=5000 \
        "${WEB_IMAGE}" > /dev/null
fi

# Output required message
echo "The app is available at http://localhost:${APP_PORT}"
