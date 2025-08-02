#!/usr/bin/bash


command_master=""
command_caves=""
cluster_name="$1"

cd "$HOME/fall.bot/scripts"

./setup.sh

if [ $2 = "True" ]
then
	command_master+="bash run_custom_server.sh $cluster_name Master True\n"
	command_caves+="bash run_custom_server.sh $cluster_name Caves True\n"
else
	command_master+="bash run_custom_server.sh $cluster_name Master False\n"
	command_caves+="bash run_custom_server.sh $cluster_name Caves False\n"
fi

screen -S s -X stuff "$command_master"
echo "starting master shard"
screen -S c -X stuff "$command_caves"
echo "starting cave shard"

