#!/usr/bin/env python3
"""Companion script for my Macro Keyboard.
Use 'me2d13/luamacros' for keyboard input grabbing.

Note: Make sure this script is run only by trusted users.
"""
from pynput.keyboard import Key, Controller
from os import system, path, getenv
import sys
import requests
import json
import paramiko
import logging
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

file_path = path.realpath(__file__)
logging.basicConfig(
    filename=f"{file_path}/../windows_macro.log",
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    encoding="utf-8",
    level=logging.WARNING,
)


def keebs_shortcut(s_key):
    """Emulate keyboard shortcuts"""
    shortcuts = {
        "snip": [Key.cmd, Key.shift, "s"],
        "vss_cmd_palette": [Key.ctrl, Key.shift, "p"],
    }
    try:
        keyboard = Controller()
        for k in shortcuts[s_key]:
            keyboard.press(k)
        for k in shortcuts[s_key]:
            keyboard.release(k)
    # skipcq: PYL-W0703
    except Exception as error:
        logging.error("keebs_shortcut: %s", error)


def turn_off_tv():
    """Turn off TV and XServer"""
    h_host = getenv("HOME_ASSISTANT_API_HOST", default=None)
    h_token = getenv("HOME_ASSISTANT_API_TOKEN", default=None)
    ssh_host = getenv("REMOTE_1_SSH_HOST", default=None)
    ssh_uname = getenv("REMOTE_1_SSH_UNAME", default=None)
    ssh_pass = getenv("REMOTE_1_SSH_PASS", default=None)
    if None in [h_host, h_token, ssh_host, ssh_uname, ssh_pass]:
        print("Enviroinment variables not found.")
        sys.exit(-1)
    headers = {"Authorization": f"Bearer {h_token}"}
    # Using SSH to stop gdm3 on the ubuntu-htpc
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=ssh_uname, password=ssh_pass)
        # skipcq: BAN-B601
        ssh.exec_command(f"echo {ssh_pass} | sudo -S systemctl stop gdm3 && exit")
        ssh.close()
    # skipcq: PYL-W0703
    except Exception as error:
        logging.error("turn_off_tv (SSH): %s", error)
    # Using Home Assistant to turn off TV
    try:
        data = {"entity_id": "media_player.samsung_tv"}
        hostname = h_host
        requests.post(
            f"{hostname}/api/services/media_player/turn_off",
            headers=headers,
            data=json.dumps(data),
        )
    # skipcq: PYL-W0703
    except Exception as error:
        logging.error("turn_off_tv (TV): %s", error)


def win_run(cmd: str):
    """Execute system commands"""
    try:
        # skipcq: BAN-B605
        system(cmd)
    # skipcq: PYL-W0703
    except Exception as error:
        logging.error("win_run: %s", error)


def main():
    if sys.argv[1] == "run":
        win_run(sys.argv[2])
    elif sys.argv[1] == "keebs":
        keebs_shortcut(sys.argv[2])
    elif sys.argv[1] == "off_tv":
        turn_off_tv()
    else:
        logging.warning("'%s'' flag does not exist.", sys.argv[1])


if __name__ == "__main__":
    main()
