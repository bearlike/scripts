#!/usr/bin/env bash
# @title: Alias and functions
# @description: Human friendly aliases and functions

: ' Personal Aliases and Functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
alias zshconfig="nano ~/.zshrc"
alias ohmyzsh="nano ~/.oh-my-zsh"
alias cls='clear' # Sometimes I forget I'm not in Windows
alias py='/bin/python3'

: ' File Operations Aliases and Functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
file-p-x() { chmod +x "$@"; }
file-p-all() { sudo chmod 777 -R "$@"; }
file-own-me() { sudo chown "$USER":"$(id -g "$USER")" -R "$@"; }

# Create a backup copy of a file
file-bk() { cp -a "$1" "$1".backup; }

# Create a backup copy of a file with date
file-bk-date () { cp -a "$1" "$1"."$(date_ddmmyyyy)".backup; }

# Create a backup copy of a file with datetime
file-bk-timedate () { cp -a "$1" "$1"."$(date_hhmmssddmmyyyy)".backup ; }

: ' Networking Aliases and Functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
# Show user ports with process names and IDs
alias net-find-uports="sudo netstat -tulpn"

# Show all IPs associated with host
alias net-ip="sudo hostname -I"

# Show all docker related aliases
net-alias() { _guide_alias_ "Net operations" "netstat\|hostname -I"; }

: ' Docker Aliases and Functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
# Docker Compose
alias d-c="docker-compose"

# Get latest container ID
alias d-l="docker ps -l -q"

# Get container process
alias d-ps="docker ps"

# Get process included stop container
alias d-pa="docker ps -a"

# Get images
alias d-i="docker images"

# Get container IP
alias d-ip="docker inspect --format '{{ .NetworkSettings.IPAddress }}'"

# Run deamonized container, e.g., $dkd base /bin/echo hello
alias d-kd="docker run -d -P"

# Run interactive container, e.g., $dki base /bin/bash
alias d-ki="docker run -i -t -P"

# Execute interactive container, e.g., $dex base /bin/bash
alias d-ex="docker exec -i -t"

# Prune all unused Docker objects
alias d-cl="docker system prune"

# Stop all containers
d-stop-all() {
    docker stop "$(docker ps -a -q)"; 
}

# Show all docker related aliases
d-alias() { 
    _guide_alias_ "Docker" "docker";
}

# Bash into a running container
# arg $1 : container name/id
d-bash() { 
    docker exec -it "$1" bash;
}

: ' User aliases ends here. Below are helpers.
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
# Helper: Text Formatting
underline=$(tput smul) # skipcq: SH-2034
nounderline=$(tput rmul) # skipcq: SH-2034
bold=$(tput bold) # skipcq: SH-2034
normal=$(tput sgr0) # skipcq: SH-2034

# Helper: function for alias index
# arg $1 : Title
# arg $2 : grep argument
_guide_alias_() {
    printf "%s%s aliases%s\n\n" "$underline" "$1" "$nounderline";
    alias | grep "$2" | sed "s/^\([^=]*\)=\(.*\)/\1 \t=>   \2/" | sed "s/['|\']//g" | sort;
} # skipcq: SH-1056