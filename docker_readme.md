# Notes for docker use in this project

## Docker compose

    docker compose build
    docker compose up -d
    docker compose down

## Python container

    docker exec -it pi-humidity-python-1 bash

## TimescaleDB container

    docker exec -it pi-humidity-timescaledb-1 psql -U postgres -d pi_humidity

## Reset everything

Stop all containers, remove them, and remove all images

    docker kill $(docker ps -q)
    docker rm $(docker ps -a -q)
    docker rmi $(docker images -q)

Remove mounted volumes

    sudo rm -rf ./postgres
    sudo rm -rf ./logs
