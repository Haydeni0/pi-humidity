import os
from dataclasses import dataclass
from pathlib import Path
import sys

from certbot.main import main as certmain

WEBSITE_HOSTNAME = os.environ.get("WEBSITE_HOSTNAME")
EMAIL = os.environ.get("EMAIL")

@dataclass
class Cert:
    certfile: Path | None
    keyfile: Path | None

    def __init__(self):
        
        certbot_path = Path(f"/etc/letsencrypt/live/{WEBSITE_HOSTNAME}")
        certfile = certbot_path.joinpath(f"fullchain.pem")
        keyfile = certbot_path.joinpath(f"privkey.pem")

        if not (certfile.exists() and keyfile.exists()):
            certfile = None
            keyfile = None
        
        self.certfile = certfile
        self.keyfile = keyfile
    
    def getSslContext(self):
        if self:
            return (self.certfile, self.keyfile)
        else:
            return None

    def __bool__(self):
        return (self.certfile is not None) and (self.keyfile is not None)

def main():
    if not Cert():
        args = ["certonly", "-d", f"{WEBSITE_HOSTNAME}", "--email", f"{EMAIL}", "--agree-tos", "--standalone", "--non-interactive"]
        sys.exit(certmain(args))

if __name__ == "__main__":
    main()
