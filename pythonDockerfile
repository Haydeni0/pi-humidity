FROM python:3.10
WORKDIR /pytest

RUN pip install --upgrade pip

# Use two different requirements files to segment the build
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY requirements2.txt .
RUN python -m pip install -r requirements2.txt