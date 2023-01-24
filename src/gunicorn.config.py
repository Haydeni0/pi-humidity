# Gunicorn settings
# https://docs.gunicorn.org/en/latest/settings.html
# https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

import os
from pathlib import Path

WEBSITE_HOSTNAME = os.environ.get("WEBSITE_HOSTNAME")

certbot_path = Path("/etc/letsencrypt/live/")

if WEBSITE_HOSTNAME is not None and certbot_path.exists():
    certfile = certbot_path.joinpath(f"{WEBSITE_HOSTNAME}/fullchain.pem")
    keyfile = certbot_path.joinpath(f"{WEBSITE_HOSTNAME}/privkey.pem")
    bind = "0.0.0.0:443"
else:
    bind = "0.0.0.0:80"

workers = 4

# pidfile = 'pidfile'
# errorlog = 'errorlog'
# loglevel = 'info'
# accesslog = 'accesslog'
# access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'