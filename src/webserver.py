from dhtPlotter import app
import os
from my_certbot import Cert, createCertificate
from datetime import datetime
import yaml
import logging

import gunicorn.app.base
from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.config import Config
import multiprocessing
import os

logger = logging.getLogger("__name__")
start_time = datetime.now()

# Based on https://stackoverflow.com/a/72186728
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


def startWebserver(dev: bool = False):
    # Set up a cronjob to renew the certificate every day at 0230
    # os.system("crontab -l > my_cron")
    os.system(r"echo 30 2 \* \* \* python /src/my_certbot.py  >> /tmp/my_cron")
    os.system("crontab /tmp/my_cron")
    os.system("rm /tmp/my_cron")

    cert = Cert()

    # Create a certificate if one doesn't already exist and a hostname is given
    if not cert and cert.getHostname():
        createCertificate()
        cert = Cert()

    if cert:
        # Certificate exists, use https
        port = 443
    else:
        # Certificate doesn't exist, use http
        port = 80

    if os.getenv("PROFILE") is not None:
        # Optional profiler that prints to the command line
        app.server.config["PROFILE"] = True  # type: ignore
        app.server.wsgi_app = ProfilerMiddleware(  # type: ignore
            app.server.wsgi_app, sort_by=("cumtime", "tottime"), restrictions=[50]  # type: ignore
        )

    if dev:
        # Use Dash instead of gunicorn for development
        ssl_context = cert.getSslContext()
        app.run_server(host="0.0.0.0", port=port, debug=True, ssl_context=ssl_context)

    else:
        # Use gunicorn
        options = {
            "bind": f"0.0.0.0:{port}",
            "workers": 1, # (multiprocessing.cpu_count() * 2) + 1,
            "certfile": cert.certfile,
            "keyfile": cert.keyfile,
            # "reload": True,
            # "preload_app" :False,
        }
        StandaloneApplication(app.server, options).run()


if __name__ == "__main__":
    """
    Gunicorn webserver for production
    Multiple processes
    """

    # Set up logging
    start_time_formatted = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # Worry about this potentially clogging up the device storage
    # if the container keeps restarting or too many things are logged...
    logging.basicConfig(
        filename=f"/shared/logs/webserver_{start_time_formatted}.log",
        filemode="w",
        format="[%(asctime)s - %(levelname)s] %(funcName)20s: %(message)s",
        level=logging.DEBUG,
    )

    startWebserver()
