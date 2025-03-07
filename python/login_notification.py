#!/usr/bin/env python
"""Retrieves `Gotify` tokens from `Simple Secrets Manager (SSM)` and sends
notification on user login. For Windows, Use task scheduler to automate."""
from datetime import datetime
from sys import platform
import requests
import logging
import getpass
import os
import sys


# Alter log path if necessary
LOG_PATH = "C:\\Files\\logs\\general.log"
logging.basicConfig(
    filename=LOG_PATH,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    level=logging.DEBUG,
)


def get_key():
    """Returns Gotify token from SSM
    Returns:
        str: Gotify Token
    """
    # Reading the SSM_URL from Enviroinment variables.
    # Ex: https://secrets.adam.home
    ssm_url = os.environ.get("SSM_URL")
    # Reading the SSM_TOKEN from Enviroinment variables.
    ssm_token = os.environ.get("SSM_TOKEN")
    if ssm_token is not None:
        path, keyname = "gotify", "SECURITY_NOTIFICATIONS"
        # https://github.com/bearlike/simple-secrets-manager
        ssm_url = f"{ssm_url}/api/secrets/kv/{path}/{keyname}"
        headers = {"X-API-KEY": ssm_token}
        # Retrying 5 times before giving up
        retries = 5
        for count in range(retries):
            try:
                response = requests.get(ssm_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    return response.json().get("value")
            except requests.exceptions.Timeout:
                logging.warning(
                    "[%s/%s] Timed-out so trying again.", str(count + 1), str(retries)
                )
            except requests.ConnectionError as error:
                logging.error(
                    "[%s/%s] Connection error to SSM: %s",
                    str(count + 1),
                    str(retries),
                    error,
                )
        logging.error("Couldn't reach SSM. Halting!")
    return None


def now():
    """Get current timestamp
    Returns:
        str: timestamp string
    """
    current_time = datetime.now()
    str_date = current_time.strftime("%d %B %Y, %I:%M:%S %p")
    return str_date


def send_notification(title, message, priority):
    secret = get_key()
    if secret is None:
        sys.exit(-1)
    gotify_url = os.environ.get("GOTIFY_URL")
    url = f"{gotify_url}/message?token={ secret }"
    head = {}
    data = {
        "title": title,
        "message": message,
        "priority": priority,
    }

    try:
        response = requests.post(url, json=data, headers=head, timeout=30)
        if response.status_code == 200:
            return True
    except requests.Timeout as error:
        logging.error("Timed Out to Gotify: %s", error)
    except requests.ConnectionError as error:
        logging.error("Connection error to Gotify: %s", error)
    except Exception as error:
        logging.error("%s", error)
    return False


def main():
    if platform in ["linux", "linux2"]:
        os_name = "linux"
    elif platform == "darwin":
        os_name = "OS X"
    elif platform == "win32":
        os_name = "Windows"
    # The below variable will be something "PCNAME (Windows)"
    hostname = f"{ os.environ.get('COMPUTERNAME').title() } ({os_name})"
    title = f"{ getpass.getuser() } Logged into { hostname }"
    logging.info(title)
    send_notification(title=title, message=f"Timestamp: { now() }", priority=8)


if __name__ == "__main__":
    main()
