# Based on https://stackoverflow.com/a/72186728
from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.config import Config
import multiprocessing
import os
from pathlib import Path

from dhtPlotter import server

import gunicorn.app.base


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

    WEBSITE_HOSTNAME = os.environ.get("WEBSITE_HOSTNAME")

    certbot_path = Path(f"/etc/letsencrypt/live/{WEBSITE_HOSTNAME}")
    certfile = certbot_path.joinpath(f"fullchain.pem")
    keyfile = certbot_path.joinpath(f"privkey.pem")

    if certfile.exists() and keyfile.exists():
        bind = "0.0.0.0:443"
    else:
        certfile = None
        keyfile = None
        bind = "0.0.0.0:80"

    workers = (multiprocessing.cpu_count() * 2) + 1

    options = {
        "bind": bind,
        "workers": workers,
        "certfile": certfile,
        "keyfile": keyfile,
    }

    return options


if __name__ == "__main__":
    options = gunicornConfig()
    StandaloneApplication(server, options).run()
