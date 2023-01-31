import os
from dataclasses import dataclass
from pathlib import Path
import sys

from certbot.main import main
from certbot.errors import Error

import logging
logger = logging.getLogger(__name__)

WEBSITE_HOSTNAME = os.environ.get("WEBSITE_HOSTNAME")
EMAIL = os.environ.get("EMAIL")


@dataclass
class Cert:
    certfile: str | None
    keyfile: str | None

    def __init__(self):

        certbot_path = Path(f"/etc/letsencrypt/live/{WEBSITE_HOSTNAME}")
        certfile = certbot_path.joinpath(f"fullchain.pem")
        keyfile = certbot_path.joinpath(f"privkey.pem")

        if not (certfile.exists() and keyfile.exists()):
            certfile = None
            keyfile = None

        self.certfile = str(certfile)
        self.keyfile = str(keyfile)

    def getSslContext(self):
        if self:
            return (self.certfile, self.keyfile)
        else:
            return None

    def getHostname(self):
        return WEBSITE_HOSTNAME

    def __bool__(self):
        return (self.certfile is not None) and (self.keyfile is not None)


def createCertificate():
    # Create a certificate using certbot
    args = [
        "certonly",
        "-d",
        f"{WEBSITE_HOSTNAME}",
        "--email",
        f"{EMAIL}",
        "--agree-tos",
        "--standalone",
        "--non-interactive",
    ]
    try:
        main(args)
    except Error as err:
        logger.error(err)





if __name__ == "__main__":
    if (WEBSITE_HOSTNAME is not None) and (EMAIL is not None):
        createCertificate()
