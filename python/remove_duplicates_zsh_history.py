#!/usr/bin/env python3

# Remove duplicates from zsh history file
# Makes sure that the history file is not bloated with duplicates
# Makes zsh-autosuggestions much better
# This script is to be run in a cron job


def remove_duplicates_from_history_file(path):
    commands = set()

    with open(path) as file:
        lines = file.readlines()

    for line in lines:
        command = line.split(";")[-1]
        commands.add(command)

    # TODO: Messes up the order of commands (timestamps)
    with open(path, "w") as file:
        begin = 1600000000
        for command in commands:
            if command in ["\n", "", " ", None]:
                continue
            file.write(f": { begin }:0;" + command)
            begin += 1


if __name__ == "__main__":
    history_path = "/home/user/.zsh_history"
    remove_duplicates_from_history_file(path=history_path)
