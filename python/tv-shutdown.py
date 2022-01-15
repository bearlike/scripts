#!/usr/bin/env python3

import samsungctl
from os import getenv
from dotenv import load_dotenv
import sys

load_dotenv()  # take environment variables from .env.

tv_id = getenv("SAMSUNG_TV_ID", default=None)
tv_host = getenv("SAMSUNG_TV_HOST", default=None)
if None in [tv_id, tv_host]:
    print("Enviroinment variables not found.")
    sys.exit(-1)

config = {
    "name": "samsungctl",
    "description": "PC",
    "id": "REPLACE WITH TV ID",
    "host": "REPLACE WITH TV IP",
    "method": "legacy",
    "port": 55000,
    "timeout": 5,
}

try:
    with samsungctl.Remote(config) as remote:
        remote.control("KEY_POWEROFF")
except OSError:
    print("No route to Host or TV...")
# skipcq: PYL-W0703
except Exception as error:
    print(f"Connection to TV error due to {error}")
