#!/usr/bin/bash

cd "$HOME/fall.bot/scripts"

command_master=""
command_caves=""
cluster_name="$1"

if [ $2 = "True" ]
then
	command_master+="bash run_custom_server.sh $cluster_name Master True^M"
	command_caves+="bash run_custom_server.sh $cluster_name Caves True^M"
else
	command_master+="bash run_custom_server.sh $cluster_name Master False^M"
	command_caves+="bash run_custom_server.sh $cluster_name Caves False^M"
fi

screen -S s -p 0 -X stuff "c_save()^M"
echo "saving server..."
sleep 5
screen -S c -p 0 -X stuff "c_shutdown()^M"
sleep 1
screen -S s -p 0 -X stuff "c_shutdown()^M"
echo "stopping server..."
sleep 20
echo "server shut down"

# delete the screen sessions to make sure it's not running
screen -S s -X quit
screen -S c -X quit

# setup again
./setup.sh

screen -S s -X stuff "$command_master"
echo "starting master shard"
sleep 10
screen -S c -X stuff "$command_caves"
echo "starting cave shard"



