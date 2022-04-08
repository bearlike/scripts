#!/usr/bin/env bash
# @title: Nextcloud Snapshot
# @description: Snapshot Nextcloud and uploads to remote locations such as Google Drive. Can be used as a Cronjob.
# Tested on Ubuntu Server 20.04 LTS

# Make sure enviroinment variables are set in .bashrc
source_path=$NC_SOURCE_PATH   # Where nextcloud is
archive_path=$NC_ARCHIVE_PATH # Where you want to store the archive
archive_password=$NC_ARCHIVE_PASSWORD
remote_path=$NC_REMOTE_PATH # rClone must be configured (eg: gdrive:snapshots)

start_time=$(date +%s)

# Variables for pretty printing
RED=$(tput bold)$(tput setaf 1)   # Red Color
GREEN=$(tput bold)$(tput setaf 2) # Green Color
NC=$(tput sgr0)                   # No Color

# Checking root/sudo permissions
if [ "$(id -u)" -ne "0" ]; then
	echo "${RED}Please run as root${NC}"
	exit
fi

backup_dir=$(date +'%d-%m-%Y')
archive_name="Nextcloud_Backup_${backup_dir}.7z"

# Deleting previous backup file(s)
rm -rf "${archive_path:?}/"*

# 7z compress and password protect file
# > sudo apt install p7zip-full
echo -e "${GREEN}Compression started....${NC}"
7z a "$archive_path"/"$archive_name" -p"$archive_password" -mhe "$source_path"
echo -e "${GREEN}Finished Compression${NC}"

# Upload to gdrive using rclone
echo -e "${GREEN}Upload started....${NC}"
rclone copy --update --verbose --transfers 1 --checkers 8 --contimeout 60s --timeout 300s --retries 3 --low-level-retries 10 --stats 1s "$archive_path" "$remote_path"
echo -e "${GREEN}Finished uploading${NC}"

end_time=$(date +%s)
runtime=$((end_time - start_time))
echo -e "${GREEN}Completed in ${runtime} seconds ${NC}"
