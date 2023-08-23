#!/bin/bash
# * Sample Output: https://i.imgur.com/dkQzkp5.jpg

# Attempt to clear screen (may not work with MOTDs)
/usr/bin/clear

# Add padding
echo -e ""

# You need an image for this to work
# Generate the image representation using chafa
# * sudo apt install -y chafa
IMAGE_OUTPUT=$(chafa --size=50 /home/user/logo.png)

# Split the image output into an array of lines
IFS=$'\n' read -rd '' -a IMAGE_LINES <<< "$IMAGE_OUTPUT"

# Colors
GREEN="\e[1;32m"
ORANGE="\e[1;33m"
RED="\e[1;31m"
YELLOW="\e[1;33m"
RESET="\e[0m"

# Icons
CHECK="✔️"
WARNING="⚠️"
ERROR="❌"

# Extract system details
HOSTNAME=$(uname -n)
ETH_IP=$(ip addr show enp0s31f6 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)
OS_VERSION=$(lsb_release -d | cut -f2)
KERNEL_VERSION=$(uname -r)
UPTIME=$(uptime -p | sed 's/up //')
LOADS=$(uptime | awk -F'load average: ' '{print $2}')
LOAD1=$(echo $LOADS | cut -d, -f1)
LOAD5=$(echo $LOADS | cut -d, -f2)
LOAD15=$(echo $LOADS | cut -d, -f3)

# Color coding and icon for load average
LOAD_COLOR=$GREEN
LOAD_ICON=$CHECK
[ $(echo "$LOAD1 > 1.0" | bc) -eq 1 ] && { LOAD_COLOR=$ORANGE; LOAD_ICON=$WARNING; }
[ $(echo "$LOAD1 > 2.0" | bc) -eq 1 ] && { LOAD_COLOR=$RED; LOAD_ICON=$ERROR; }

# RAM details
RAM_USED_MB=$(free -m | awk 'NR==2{print $3}')
RAM_TOTAL_MB=$(free -m | awk 'NR==2{print $2}')
RAM_USAGE_PERCENT=$(awk "BEGIN {printf \"%.2f\", ($RAM_USED_MB/$RAM_TOTAL_MB)*100}")

# Color coding and icon for RAM usage
RAM_COLOR=$GREEN
RAM_ICON=$CHECK
[ $(echo "$RAM_USAGE_PERCENT > 70" | bc) -eq 1 ] && { RAM_COLOR=$ORANGE; RAM_ICON=$WARNING; }
[ $(echo "$RAM_USAGE_PERCENT > 90" | bc) -eq 1 ] && { RAM_COLOR=$RED; RAM_ICON=$ERROR; }

# Disk details
DISK_USED_GB=$(df -h / | awk 'NR==2 { print $3 }')
DISK_USAGE_PERCENT_RAW=$(df / | awk 'NR==2 { print $5 }' | tr -d '%')
DISK_USAGE_PERCENT="${DISK_USAGE_PERCENT_RAW}%"

# Color coding and icon for Disk usage
DISK_COLOR=$GREEN
DISK_ICON=$CHECK
[ $DISK_USAGE_PERCENT_RAW -gt 70 ] && { DISK_COLOR=$ORANGE; DISK_ICON=$WARNING; }
[ $DISK_USAGE_PERCENT_RAW -gt 90 ] && { DISK_COLOR=$RED; DISK_ICON=$ERROR; }

# Define the information to be displayed alongside the image
INFO=(
    "${GREEN}Welcome to your Home Server!${RESET}"
    "${YELLOW}═════════════════════════════════════════════${RESET}"
    "\e[1;34mHostname    \e[0m: $HOSTNAME"
    "\e[1;34mEthernet IP \e[0m: $ETH_IP"
    "\e[1;34mOS Version  \e[0m: $OS_VERSION"
    "\e[1;34mKernel      \e[0m: $KERNEL_VERSION"
    "\e[1;34mUptime      \e[0m: $UPTIME"
    "\e[1;34mLoad Average\e[0m: ${LOAD_COLOR}$LOAD_ICON $LOAD1, $LOAD5, $LOAD15${RESET}"
    "\e[1;34mRAM Usage   \e[0m: ${RAM_COLOR}$RAM_ICON $RAM_USED_MB MB of $RAM_TOTAL_MB MB ($RAM_USAGE_PERCENT)${RESET}"
    "\e[1;34mDisk Usage  \e[0m: ${DISK_COLOR}$DISK_ICON $DISK_USED_GB used ($DISK_USAGE_PERCENT)${RESET}"
    "${YELLOW}──────────────────────────────────────────────${RESET}"
    "${ORANGE}Don't bother! You'd fuck it up anyways.${RESET}"
)

# Print the image and information side-by-side with padding and separator
for i in "${!IMAGE_LINES[@]}"; do
    echo -e "${IMAGE_LINES[$i]}   ${YELLOW}║${RESET}   ${INFO[$i]}"
done

echo -e ""

# Get the last login information for the "abc" user
LAST_LOGIN=$(last -n 1 kk | head -n 1 | awk '{print "Last login: " $4 " " $5 " " $6 " " $7 " " $8 " from " $3}')

# Print the last login information in yellow
echo -e "${YELLOW}✿ $LAST_LOGIN ✿${RESET}"
echo -e ""
