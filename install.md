# Installation instructions

## Physical installation instructions

## Software installation instructions

Update

    sudo apt-get update

Install docker

    sudo apt-get remove docker docker-engine docker.io containerd runc
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh

Clone this repository

    git clone git@github.com:Haydeni0/pi-humidity.git
    cd pi-humidity

Run ```./setup.bash``` to set the database password and set up initial config (including DHT22 sensor names and their corresponding GPIO pins). This writes to ```./password.env``` and ```./shared/config.yaml``` respectively, which can be edited by hand to change further parameters.

    ./setup.bash

Run Docker

> ***Development notes***
>
> To build the container use the docker file [```./pythonDockerfile```](./pythonDockerfile)
>
> The build may take a *long* time on a raspberry pi.
> > It is recommended to use a faster computer using ```docker buildx build``` to build for ```linux/arm/v7```, and optionally for ```linux/amd64```.
> >
> >     docker buildx create --name mybuilder --driver docker-container --bootstrap
> >     docker buildx use mybuilder
> >     docker buildx build -f python.Dockerfile . -t haydeni0/pi-humidity:python --platform linux/arm/v7,linux/amd64
>
>     docker build -f pythonDockerfile . -t haydeni0/pi-humidity:python
>     docker push haydeni0/pi-humidity:python

Use images available on docker hub, specified in the compose file. Run the command:

    docker compose up -d

Now, if the GPIO pins are set correctly, this will display the temperature and humidity graphs to port 80 of the raspberry pi, and can be seen by entering in the local ip of the pi into a web browser from a computer on the same LAN (or localhost on a browser in the GUI of the raspberry pi).

The TimescaleDB database containing the sensor data is accessible on port 5432 of the raspberry pi (Username ```postgres``` and password set in ```./password.env```). This also can be accessed through the raspberry pi command line with docker (schema and table names defined in ```./config.yaml```)

    docker exec -it pi-humidity-timescaledb /bin/bash -c 'psql -U postgres -d ${POSTGRES_DB}'

    SELECT * FROM dht ORDER BY dtime DESC LIMIT 10;
