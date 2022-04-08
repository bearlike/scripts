#!/bin/bash

# Checking root/sudo permissions
if [ "$(id -u)" -ne "0" ]; then
    echo "Please run as root."
    exit
fi
# Make sure hplip is installed
scanimage > /home/pi/Scans/$(date +"%F_%H.%M.%S_%Z").png --format png --resolution=200 --mode=Color -p
