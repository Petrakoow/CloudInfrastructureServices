#!/bin/bash

FLASK_CONTAINER_ID=$(docker ps -q --filter "ancestor=lab-5-web")

if [ -z "$FLASK_CONTAINER_ID" ]; then
    echo "Flask container not found"
    exit 1
fi

docker exec -i $FLASK_CONTAINER_ID flask db init
docker exec -i $FLASK_CONTAINER_ID flask db migrate -m "Initial migration"
docker exec -i $FLASK_CONTAINER_ID flask db upgrade
