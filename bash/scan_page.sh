#!/usr/bin/env bash
# @title: Scan Pages
# @description: Scan a page from my HP flatbed scanner through SANE (Scanner Access Now Easy) interface

# Checking root/sudo permissions
if [ "$(id -u)" -ne "0" ]; then
    echo "Please run as root."
    exit
fi
mkdir -p ~/Scans
# Make sure hplip is installed and SANE is configured
# Should change depending on the scanner, this works on HP Deskjet 5800 series
scanimage >~/Scans/$(date +"%F_%H.%M.%S_%Z").png --format png --resolution=200 --mode=Color -p
