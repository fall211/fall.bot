#!/usr/bin/bash

screen -S s -X stuff "c_save()\n"
sleep 5
screen -S c -X stuff "c_shutdown()\n"
sleep 1
screen -S s -X stuff "c_shutdown()\n"
sleep 15

# delete the screen session
screen -S s -X quit
screen -S c -X quit