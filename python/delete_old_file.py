#!/usr/bin/env python3
# Service script for TorrentBox to periodically deletes files from a directory.
# Use systemctl to init a service.
import os
from datetime import datetime
import logging

logging.basicConfig(filename='delete_service.log',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    encoding='utf-8', level=logging.DEBUG)


def run(
        path="/mnt/Downloads",
        exceptions=["/mnt/Downloads/script", "/mnt/Downloads/qbittorrent"],
        max_days=10
):
    """
    Args:
        path (str, optional): Path to scan for deletion.
        exceptions (list, optional): List of directory paths to be excempted.
        max_days (int, optional): Number of days.
    """
    logging.info("Service started...")
    del_size, del_count = 0, 0
    try:
        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                if not any(map(file_path.__contains__, exceptions)) and \
                        not file_path.endswith(".!qb"):
                    modified_time = datetime.fromtimestamp(
                        os.path.getmtime(file_path))
                    today = datetime.today()
                    file_age = today - modified_time
                    if file_age.days >= max_days:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        del_count += 1
                        del_size += file_size
                        logging.debug(
                            f"Deleted '{file_path}', Modified on '{modified_time:%d-%m-%Y %H:%M}', of size '{file_size} bytes'")
        logging.info(
            f"Service finished. Deleted {del_count} files of {del_size} bytes")
    except Exception as _err:
        logging.error(f"Service interrupted. {_err}")
        logging.error(
            f"Deleted {del_count} files of {del_size} bytes until error.")


if __name__ == "__main__":
    run(max_days)
