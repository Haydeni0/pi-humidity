# Notes for docker use in this project

## TimescaleDB toolkit (more hyperfunctions)
This isn't available as a docker container in linux/arm yet, see github [issue](https://github.com/timescale/timescaledb-docker-ha/issues/259).

## Docker compose

    docker compose build
    docker compose up -d
    docker compose down

## Python container

    docker exec -it pi-humidity-dhtplotter-1 bash

## TimescaleDB container

Connect to database

    docker exec -it pi-humidity-timescaledb /bin/bash -c 'psql -U postgres -d ${POSTGRES_DB}'

View table entries

    SELECT * FROM test.dht_inside ORDER BY dtime DESC LIMIT 10;

## Reset everything

Stop all containers, remove them, and remove all images

    docker kill $(docker ps -q)
    docker rm $(docker ps -a -q)
    docker rmi $(docker images -q)

Remove mounted volumes

    sudo rm -rf ./postgres
    sudo rm -rf ./logs
