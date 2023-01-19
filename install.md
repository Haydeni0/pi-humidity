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

Add password to an environment file (change ```my_postgres_password``` to something else)

    echo POSTGRES_PASSWORD=my_postgres_password > password.env

Run Docker

> ***Development notes***
>
> To build the container use the docker file [```./pythonDockerfile```](./pythonDockerfile)
>
> The build may take a *long* time on a raspberry pi.
> > It is recommended to use a faster computer using ```docker buildx build``` to build for ```linux/arm/v7```, and optionally for ```linux/amd64```.
> >
> >     docker buildx build -f pythonDockerfile . -t haydeni0/pi-humidity:python --platform linux/arm/v7,linux/amd64
>
>     docker build -f pythonDockerfile . -t haydeni0/pi-humidity:python
>     docker push haydeni0/pi-humidity:python

Use images available on docker hub, specified in the compose file. Run the command:

    docker compose up -d
