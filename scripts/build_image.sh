#!/bin/bash

# Registry name
ENV=$1
SERVICE=$2
REGISTRY_PROJECT="devlaundromat"
REGISTRY_USER="devlaundromat"

if [ -z "$SERVICE" ]; then
    SERVICE="backend"
    echo "No service specified, defaulting to backend."
fi

# Determine environment suffix
if [ -z "$ENV" ]; then
    ENV_SUFFIX=""
    echo "No environment specified, using default tag."
elif [ "$ENV" == "prod" ] || [ "$ENV" == "production" ]; then
    ENV_SUFFIX="production"
elif [ "$ENV" == "stag" ] || [ "$ENV" == "staging" ]; then
    ENV_SUFFIX="staging"
else
    echo "Invalid environment: ${ENV}. Valid options are: prod, production, stag, staging"
    exit 1
fi

if [ "$SERVICE" == "backend" ]; then
    SERVICE_NAME="lms-backend"
elif [ "$SERVICE" == "mqtt-consumer" ]; then
    SERVICE_NAME="lms-mqtt-consumer"
elif [ "$SERVICE" == "celery-beat" ]; then
    SERVICE_NAME="lms-celery-beat"
elif [ "$SERVICE" == "celery-worker" ]; then
    SERVICE_NAME="lms-celery-worker"
else
    echo "Invalid service: ${SERVICE}"
    exit 1
fi

# Select Dockerfile based on service
if [ "$SERVICE" == "backend" ]; then
    DOCKERFILE="dockerfiles/backend.Dockerfile"
elif [ "$SERVICE" == "mqtt-consumer" ]; then
    DOCKERFILE="dockerfiles/mqtt_consumer.Dockerfile"
elif [ "$SERVICE" == "celery-beat" ]; then
    DOCKERFILE="dockerfiles/celery-beat.Dockerfile"
elif [ "$SERVICE" == "celery-worker" ]; then
    DOCKERFILE="dockerfiles/celery-worker.Dockerfile"
fi

# Get the current timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Try to get git commit hash if available
GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")

# Generate unique tag with environment suffix
TAG="${SERVICE_NAME}_${ENV_SUFFIX}:${TIMESTAMP}_${GIT_HASH}"

# Build the image
echo "Building Docker image with tag: ${TAG} using Dockerfile: ${DOCKERFILE}"
docker build -t ${TAG} --platform linux/amd64 -f ${DOCKERFILE} .
echo "Image built successfully!"

# Tag as latest
docker tag ${TAG} ${REGISTRY_PROJECT}/${TAG}

echo "Image tag: ${TAG}"
echo "Registry image tag: ${REGISTRY_PROJECT}/${TAG}"

docker push ${REGISTRY_PROJECT}/${TAG}
