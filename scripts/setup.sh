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

# check if screen sessions named "s" and "c" are running, if not, start them
if ! screen -list | grep -q "s"; then
    screen -dmS s
    # change to the bot directory
    screen -S s -X stuff "cd $HOME/fall.bot^M"
fi

if ! screen -list | grep -q "c"; then
    screen -dmS c
    # change to the bot directory
    screen -S c -X stuff "cd $HOME/fall.bot^M"
fi

