#!/usr/bin/env bash
# @title: Raspberry Pi MOTD
# @description: Raspberry Pi MOTD that displays basic system information on login.

print_line() {
    for i in {0..50..1}; do
        printf "─"
    done
}

title="SSH: $(hostname)"
echo -e '\033]2;'$title'\007'

# tput Color Table dict
declare -A colors
colors['RED']="tput setaf 1"
colors['GREEN']="tput setaf 2"
colors['YELLOW']="tput setaf 3"
colors['BOLD']="tput bold"
colors['RESET']="tput sgr0"

# Print Hostname
${colors['YELLOW']}

if [ $(which toilet 2>/dev/null || false) ]; then
    toilet -F metal -f smmono12 $(hostname)
elif [ $(which figlet 2>/dev/null || false) ]; then
    figlet $(hostname)
    print_line
else
    echo "Hostname: $(hostname)"
fi

let upSeconds="$(/usr/bin/cut -d. -f1 /proc/uptime)"
let secs=$((${upSeconds} % 60))
let mins=$((${upSeconds} / 60 % 60))
let hours=$((${upSeconds} / 3600 % 24))
let days=$((${upSeconds} / 86400))
UPTIME=$(printf "%d days, %02dh %02dm %02ds" "$days" "$hours" "$mins" "$secs")

# get the load averages
read one five fifteen rest </proc/loadavg
${colors['GREEN']}
echo "
$(date +"%A, %e %B %Y, %r")"
${colors['RESET']}

int() {
    expr ${1:-} : '[^0-9]*\([0-9]*\)' 2>/dev/null || :
}

# Temperature
TEMP=$(vcgencmd measure_temp | tail -c 7)
TEMP=${TEMP::-2}
TEMP_STR=$(int $TEMP)

# OK Temperature
if [ $TEMP_STR -lt 43 ]; then
    TEMP_STR=$(echo "$(${colors['BOLD']})$(${colors['GREEN']})$TEMP oC (Cool \uf058) $(${colors['RESET']})")
# Warm Temperature
elif [ $TEMP_STR -lt 55 ]; then
    TEMP_STR=$(echo "$(${colors['BOLD']})$(${colors['YELLOW']})$TEMP oC (Warm \uf071) $(${colors['RESET']})")
# Hot Temperature
elif [ $TEMP_STR -gt 55 ]; then
    TEMP_STR=$(echo "$(${colors['BOLD']})$(${colors['RED']})$TEMP oC (Hot \uf737) $(${colors['RESET']})")
fi

printf "-$(${colors['BOLD']}) Uptime $(${colors['RESET']})            : ${UPTIME}"
printf "-$(${colors['BOLD']}) Temperature $(${colors['RESET']})       : ${TEMP_STR}"
printf "-$(${colors['BOLD']}) Memory $(${colors['RESET']})            : $(free | grep Mem | awk '{print $3/1024}') MB (Used) / $(cat /proc/meminfo | grep MemTotal | awk {'print $2/1024'}) MB (Total)"
printf "-$(${colors['BOLD']}) Load Averages $(${colors['RESET']})     : ${one}, ${five}, ${fifteen} (1, 5, 15 min)"
printf "-$(${colors['BOLD']}) Running Processes $(${colors['RESET']}) : $(ps ax | wc -l | tr -d ' ')"
printf "-$(${colors['BOLD']}) LAN IP $(${colors['RESET']})            : $(ifconfig eth0 | egrep -o 'inet [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | cut -d' ' -f2) (eth0)"
# Comment Newline if necessary
printf "\n\n"
