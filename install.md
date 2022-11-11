# Installation instructions

Update

    sudo apt-get update

Install docker

    sudo apt-get remove docker docker-engine docker.io containerd runc
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh

Clone this repository

    git clone git@github.com:Haydeni0/pi-humidity.git
    cd pi-humidity

Add password to an environment file (change ```my_password``` to something else)

    echo POSTGRES_PASSWORD=my_password > password.env

Use docker compose to build and run containers

    docker compose build
    docker compose up -d
