#!/usr/bin/env python3
""" Companion script for my Macro Keyboard.
Use 'me2d13/luamacros' for keyboard input grabbing.
"""
from pynput.keyboard import Key, Controller
from os import system, environ, path
from sys import argv
import requests
import json
import paramiko
import logging

file_path = path.realpath(__file__)
logging.basicConfig(filename=f'{file_path}/../windows_macro.log',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    encoding='utf-8', level=logging.WARNING)


def keebs_shortcut(s_key):
    """ Emulate keyboard shortcuts
    """
    shortcuts = {
        "snip": [Key.cmd, Key.shift, 's'],
        "vss_cmd_palette": [Key.ctrl, Key.shift, 'p']
    }
    try:
        keyboard = Controller()
        for k in shortcuts[s_key]:
            keyboard.press(k)
        for k in shortcuts[s_key]:
            keyboard.release(k)
    except Exception as error:
        logging.error(f"keebs_shortcut: {error}")


def turn_off_tv():
    """ Turn off TV and XServer
    """
    headers = {
        'Authorization': f"Bearer {environ['HOME_ASS_API_KEY']}"
    }
    # Using SSH to stop gdm3 on the ubuntu-htpc
    try:
        ssh = paramiko.SSHClient()
        ssh_pass = environ['SSH_APOLLO_PASS']
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("192.168.1.16", username="kk", password=ssh_pass)
        ssh.exec_command(
            f"echo {ssh_pass} | sudo -S systemctl stop gdm3 && exit")
        ssh.close()
    except Exception as error:
        logging.error(f"turn_off_tv (SSH): {error}")
    # Using Home Assistant to turn off TV
    try:
        data = {"entity_id": "media_player.samsung_tv"}
        hostname = "http://192.168.1.29:8123"
        requests.post(
            f'{hostname}/api/services/media_player/turn_off',
            headers=headers,
            data=json.dumps(data)
        )
    except Exception as error:
        logging.error(f"turn_off_tv (TV): {error}")


def win_run(cmd: str):
    """ Execute system commands
    """
    try:
        system(cmd)
    except Exception as error:
        logging.error(f"win_run: {error}")


def main():
    if argv[1] == "run":
        win_run(argv[2])
    elif argv[1] == "keebs":
        keebs_shortcut(argv[2])
    elif argv[1] == "off_tv":
        turn_off_tv()
    else:
        logging.warning(f"'{argv[1]}'' flag does not exist.")


if __name__ == "__main__":
    main()
