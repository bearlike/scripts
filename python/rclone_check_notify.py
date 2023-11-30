#!/usr/bin/env python3

import subprocess
import requests
import logging
import sys
import re

# Set the logging level
logging.basicConfig(
    filename="/var/log/rclone_check.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def send_notification(title, message, priority):
    secret = os.environ.get("GOTIFY_TOKEN")
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


def run_command(command):
    try:
        # Run the command
        result = subprocess.run(
            command, capture_output=True, text=True, shell=True)

        # Return the output or error based on the execution result
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"


def check_rclone_and_fuse():
    # Check the rclone token status
    rclone_command = ["rclone about gdrive_svce:"]
    rclone_output = run_command(rclone_command)

    # Pattern to match rclone output
    pattern = r"Total:\s+\S+\s+Used:\s+\S+\s+Free:\s+\S+\s+Trashed:\s+\S+\s+Other:\s+\S+"
    if "Error:" in rclone_output or not re.match(pattern, rclone_output):
        return False, "Rclone check failed: " + rclone_output

    # Check if the filesystem type is 'fuse.rclone'
    fuse_command = "df -P -T /media_files/gdrive | tail -n +2 | awk '{print $2}'"
    fuse_output = run_command(fuse_command)
    if fuse_output != "fuse.rclone":
        return False,  "FUSE check failed: Unexpected filesystem type: " + fuse_output

    # Check the status of 'drivemount.service'
    service_command = "sudo systemctl is-active --quiet drivemount.service && echo True"
    service_status = run_command(service_command)
    if service_status != "True":
        return False, "Service check failed: drivemount.service is not active."
    return True, "All checks passed: Rclone, FUSE, and Service are all active."


def main():
    # Run the combined check
    combined_check_result, log_message = check_rclone_and_fuse()
    if not combined_check_result:
        send_notification("Rclone Check Failed", log_message, 8)
        logging.error(log_message)
        sys.exit(-1)
    else:
        logging.info(log_message)
        send_notification("Rclone Check Success", log_message, 1)


if __name__ == "__main__":
    main()
