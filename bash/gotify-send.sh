#!/usr/bin/env bash
# @title: Send notifications via gotify
# @description: Send notifications via gotify
# @usage: gotify-send.sh -t "title" -m "message" --secret ABCDEFGHIJKLMN

HOST="https://gotify.adam.home"
function usage() {
    cat <<USAGE
    Usage: $0 [-s secret] [-t title] [-m message] 
    Options:
        -s, --secret:       Gotify App Secret
        -t, --title:        Notification title
        -m, --message:      Notification message
USAGE
    exit 1
}

# if no arguments are provided, return usage function
if [ $# -eq 0 ]; then
    usage # run usage function
    exit 1
fi

while [ "$1" != "" ]; do
    case $1 in
    -s | --secret)
        AUTH_TOKEN=$2
        shift
        ;;
    -t | --title)
        TITLE=$2
        shift
        ;;
    -m | --message)
        MESSAGE=$2
        shift
        ;;
    -h | --help)
        usage # run usage function on help
        exit 1
        ;;
    *)
        usage # run usage function if wrong argument provided
        exit 1
        ;;
    esac
    shift # remove the current value for `$1` and use the next
done

if [ "$AUTH_TOKEN" = "" ] || [ "$TITLE" = "" ] || [ "$MESSAGE" = "" ]; then
    echo "Arguments cannot be empty. Add -h flag for help."
    exit 1
fi

curl "${HOST}/message?token=${AUTH_TOKEN}" -F "title=${TITLE}" -F "message=${MESSAGE}" -F "priority=1"
