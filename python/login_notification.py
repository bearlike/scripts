#!/usr/bin/env python
""" Retrieves `Gotify` tokens from `Simple Secrets Manager (SSM)` and sends
notification on user login. For Windows, Use task scheduler to automate."""
import requests
from datetime import datetime
import getpass
import os
import logging

# Alter log path if necessary
LOG_PATH = "C:\\Files\\logs\\general.log"
logging.basicConfig(filename=LOG_PATH,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    level=logging.DEBUG)


def get_key():
    """ Returns Gotify token from SSM
    Returns:
        str: Gotify Token
    """
    # Reading the SSM_TOKEN from Enviroinment variables.
    ssm_token = os.environ.get("SSM_TOKEN", None)
    if ssm_token is not None:
        path, keyname = "gotify", "SECURITY_NOTIFICATIONS"
        # https://github.com/bearlike/simple-secrets-manager
        ssm_url = f"https://secrets.adam.home/api/secrets/kv/{path}/{keyname}"
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
                    f"[{count+1}/{retries}] Timed-out so trying again.")
            except requests.ConnectionError as error:
                logging.error(
                    f"[{count+1}/{retries}] Connection error to SSM: {error}")
        logging.error("Couldn't reach SSM. Halting!")
        exit(-1)


def now():
    """ Get current timestamp
    Returns:
        str: timestamp string
    """
    current_time = datetime.now()
    str_date = current_time.strftime("%d %B %Y, %I:%M:%S %p")
    return str_date


def send_notification(title, message, priority):
    secret = get_key()
    url = f"https://gotify.adam.home/message?token={ secret }"
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
        logging.error(f"Timed Out to Gotify: {error}")
    except requests.ConnectionError as error:
        logging.error(f"Connection error to Gotify: {error}")
    except Exception as error:
        logging.error(f"{error}")
    return False


def main():
    hostname = "Shark-PC (Windows)"
    title = f"{ getpass.getuser() } Logged into { hostname }"
    logging.info(title)
    send_notification(
        title=title,
        message=f"Timestamp: { now() }",
        priority=8
    )


if __name__ == "__main__":
    main()
