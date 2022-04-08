#!/usr/bin/env bash
# @title: Raspberry Pi MOTD
# @description: Raspberry Pi MOTD that displays basic system information on login.

print_line() {
    for _ in {0..50..1}; do
        printf "-"
    done
}

title="Welcome: $(hostname)"
echo -e "\033]2;$title\007"

# tput Colors
RED="tput setaf 1"
GREEN="tput setaf 2"
YELLOW="tput setaf 3"
BOLD="tput bold"
RESET="tput sgr0"

# Print Hostname
${YELLOW}

if [ "$(which toilet 2>/dev/null || false)" ]; then
    toilet -F metal -f smmono12 "$(hostname)"
elif [ "$(which figlet 2>/dev/null || false)" ]; then
    figlet "$(hostname)"
    print_line
else
    echo "Hostname: $(hostname)"
fi

let upSeconds="$(/usr/bin/cut -d. -f1 /proc/uptime)"
let secs=$((upSeconds % 60))
let mins=$((upSeconds / 60 % 60))
let hours=$((upSeconds / 3600 % 24))
let days=$((upSeconds / 86400))
UPTIME=$(printf "%d days, %02dh %02dm %02ds" "$days" "$hours" "$mins" "$secs")

# get the load averages
read one five fifteen rest </proc/loadavg
${GREEN}
date +"%A, %e %B %Y, %r"
${RESET}

int() {
    expr "${1:-}" : '[^0-9]*\([0-9]*\)' 2>/dev/null || :
}

# Temperature
TEMP=$(vcgencmd measure_temp | tail -c 7)
TEMP=${TEMP::-2}
TEMP_STR=$(int "$TEMP")

# OK Temperature
if [ "$TEMP_STR" -lt 46 ]; then
    TEMPERATURE_COLOR=${GREEN}
    TEMP_STR="$TEMP oC (Cool)"
# Warm Temperature
elif [ "$TEMP_STR" -lt 55 ]; then
    TEMPERATURE_COLOR=${YELLOW}
    TEMP_STR="$TEMP oC (Warm)"
# Hot Temperature
elif [ "$TEMP_STR" -gt 55 ]; then
    TEMPERATURE_COLOR=${RED}
    TEMP_STR="$TEMP oC (Hot)"
fi

# Memory Used
MEM_USED=$(free | grep Mem | awk '{print $3/1024}')
MEM_TOTAL=$(cat /proc/meminfo | grep MemTotal | awk '{print $2/1024}')

# Processes
RUNNING_PROC=$(ps ax | wc -l | tr -d ' ')

# IP Address
IP_ADDRESS=$(ifconfig eth0 | egrep -o 'inet [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | cut -d' ' -f2)

printf "\n-%s Uptime %s            : %s"                            "$(${BOLD})" "$(${RESET})" "${UPTIME}"
printf "\n-%s Temperature %s       : %s%s%s"                        "$(${BOLD})" "$(${RESET})" "$($TEMPERATURE_COLOR)" "${TEMP_STR}" "$(${RESET})"
printf "\n-%s Memory %s            : %s MB (Used) / %s MB (Total)"  "$(${BOLD})" "$(${RESET})" "${MEM_USED}" "${MEM_TOTAL}"
printf "\n-%s Load Averages %s     : %s, %s, %s (1, 5, 15 min)"     "$(${BOLD})" "$(${RESET})" "${one}" "${five}" "${fifteen}"
printf "\n-%s Running Processes %s : %s"                            "$(${BOLD})" "$(${RESET})" "${RUNNING_PROC}"
printf "\n-%s LAN IP %s            : %s (eth0)"                     "$(${BOLD})" "$(${RESET})" "${IP_ADDRESS}"
# Comment Newline if necessary
printf "\n\n"
