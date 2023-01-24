# Based on https://stackoverflow.com/a/72186728
import multiprocessing
import os
from pathlib import Path

import gunicorn.app.base
from gunicorn.config import Config

from dhtPlotter import server, app
from my_certbot import Cert


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    cfg: Config

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def gunicornConfig() -> dict:

    cert = Cert()

    if cert:
        bind = "0.0.0.0:443"
    else:
        bind = "0.0.0.0:80"

    workers = (multiprocessing.cpu_count() * 2) + 1

    options = {
        "bind": bind,
        # "workers": workers, # Currently not working with multiple workers, gunicorn has weird interactions with psycopg2 with forked processes...
        "certfile": str(cert.certfile),
        "keyfile": str(cert.keyfile),
        "reload": True,
        "preload_app": False, # To stop this error https://github.com/psycopg/psycopg2/issues/281#issuecomment-985387977
    }

    return options


if __name__ == "__main__":
    # options = gunicornConfig()
    # StandaloneApplication(server, options).run()

    cert = Cert()

    if cert:
        port = 443
    else:
        port = 80
    ssl_context = cert.getSslContext()
    app.run_server(host="0.0.0.0", port = port, debug=True, ssl_context=ssl_context)
