import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from certbot.errors import Error

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
            self.certfile = None
            self.keyfile = None
        else:
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
        # Certbot isn't meant to be run through another python script it seems (from certbot.main import main)
        # This messes up logging (and probably some other things).
        # Just run certbot using command line:
        subprocess.run(["/usr/local/bin/certbot"] + args)
    except Error as err:
        logger.error(err)


if __name__ == "__main__":
    if (WEBSITE_HOSTNAME is not None) and (EMAIL is not None):
        createCertificate()
    else:
        raise ValueError(
            f"""Either WEBSITE_HOSTNAME ({WEBSITE_HOSTNAME}) or EMAIL ({EMAIL}) are not set.
            Certificate has not been renewed."""
        )
