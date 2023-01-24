# Based on https://stackoverflow.com/a/72186728
import multiprocessing
import os
from pathlib import Path

from dhtPlotter import server, app
from my_certbot import Cert, createCertificate


if __name__ == "__main__":
    # Set up a cronjob to renew the certificate every day at 0030
    os.system("crontab -l > my_cron")
    os.system("echo 30 \* \* \* \* python /src/my_certbot.py  >> /tmp/my_cron")
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

    # Use Dash instead of gunicorn for the webserver
    ssl_context = cert.getSslContext()
    app.run_server(host="0.0.0.0", port=port, debug=True, ssl_context=ssl_context)
