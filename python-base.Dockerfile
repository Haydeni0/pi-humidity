FROM python:3.10.9-bullseye
WORKDIR /build_workdir

RUN apt-get update

RUN python -m pip install --upgrade pip

# Typical libraries (takes a *long* time to build for arm/v7 due to having to build python wheels)
COPY ./requirements.txt .
RUN python -m pip install -r ./requirements.txt
