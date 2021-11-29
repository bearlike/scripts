#!/usr/bin/env bash
# Last Updated June 2, 2020
# Tested on Ubuntu Server 20.04 LTS

# Variables for pretty printing
RED=`tput bold``tput setaf 1` # Red Color
GREEN=`tput bold``tput setaf 2` # Green Color
NC=`tput sgr0` # No Color
BEGIN=$(df /home --output=used | grep -Eo '[0-9]+')

# Checking root/sudo permissions
if [ "$(id -u)" -ne "0" ]; then 
	echo "${RED}Please run as root${NC}"
	exit
fi

# Removing unused packages and cache (APT)
echo -e "${RED}Cleaning Unused Packages...${NC}" && \
sudo apt-get -y autoremove --purge && \
sudo apt-get clean && \

# Removing Old Unused Linux Kernels
IN_USE=$(uname -a | awk '{ print $3 }')
echo -e "${GREEN}Your in use kernel is ${IN_USE} ${NC}"
OLD_KERNELS=$(
    dpkg --list |
        grep -v "$IN_USE" |
        grep -Ei 'linux-image|linux-headers|linux-modules' |
        awk '{ print $2 }'
)
if [ "${#files[@]}" -ne "0" ]; then
    echo -e "\n${GREEN}Old Kernels to be removed:${NC}"
    echo -e "${GREEN}$OLD_KERNELS${NC}\n"
    read -r -p "${RED}Do you want to delete the old kernels? [y/N]${NC} " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
                for PACKAGE in $OLD_KERNELS; do
                    yes | apt purge "$PACKAGE"
                done
                ;;
            *)
                echo -e "${RED}Skipping Removing old kernel...${NC}"
                ;;
    esac
else
    echo -e "${GREEN}No old unused kernel to clean.${NC}"
fi

# Cleaning Thumbnail Cache
echo -e "${RED}Cleaning Thumbnails...${NC}" && \
sudo rm -rf ~/.cache/thumbnails/* && \

# Pruning Docker Objects
echo -e "${RED}Pruning Docker images, volumes, and networks...${NC}" && \
docker image prune -a -f --filter "until=24h" && \
docker volume prune -f && \
docker network prune -f

# Summarization
END=$(df /home --output=used | grep -Eo '[0-9]+')
RECLAIMED=$(expr $BEGIN - $END)
if [ $RECLAIMED -lt 0 ]; then
    RECLAIMED=0
fi
echo "${GREEN}${RECLAIMED} KB Reclaimed. ${NC}"

