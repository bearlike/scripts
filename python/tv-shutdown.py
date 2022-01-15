#!/usr/bin/env python3

import samsungctl
import sys

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
except Exception as error:
    print(f"Connection to TV error due to {error}")
