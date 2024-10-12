#!/usr/bin/bash

# this script sets up the environment for the discord bot to be able to control the server

function fail()
{
	echo Error: "$@" >&2
	exit 1
}

function check_for_file()
{
	if [ ! -e "$1" ]; then
		fail "Missing file: $1"
	fi
}

function check_for_dir()
{
    if [ ! -d "$1" ]; then
        fail "Missing directory: $1"
    fi
}


# Check if the "s" screen session is running
if ! screen -list | grep -q "\.s"; then
    screen -dmS s  # Start the "s" session in detached mode
    # Send the command to change to the bot directory in the "s" session
    screen -S s -X stuff "cd $HOME/fall.bot\n"
    echo "screen session s started"
fi

# Check if the "c" screen session is running
if ! screen -list | grep -q "\.c"; then
    screen -dmS c  # Start the "c" session in detached mode
    # Send the command to change to the bot directory in the "c" session
    screen -S c -X stuff "cd $HOME/fall.bot\n"
    echo "screen session c started"
fi

echo "Environment setup complete"

