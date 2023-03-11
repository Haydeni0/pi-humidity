FROM haydeni0/pi-humidity:python-base
WORKDIR /build_workdir

RUN apt-get update

RUN python -m pip install --upgrade pip

# Requirements for pyopenssl (cryptography) https://github.com/pyca/cryptography/blob/main/docs/installation.rst#debianubuntu
RUN apt-get install -y build-essential libssl-dev libffi-dev python3-dev cargo pkg-config
RUN python -m pip install pyopenssl

# Webserver related
RUN python -m pip install gunicorn
RUN python -m pip install certbot
RUN apt-get install -y cron

# Dash extra stuff
RUN python -m pip install dash_daq
RUN python -m pip install Flask-Caching
RUN python -m pip install dash-extensions

# Requirements for kaleido
RUN python -m pip install kaleido
RUN apt-get install -y libnss3-dev libgdk-pixbuf2.0-dev libgtk-3-dev libxss-dev
