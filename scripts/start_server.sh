#!/usr/bin/bash


command_master=""
command_caves=""
cluster_name="$1"

cd "$HOME/fall.bot/scripts"

./setup.sh

if [ $2 = "True" ]
then
	command_master+="bash run_custom_server.sh $cluster_name Master True^M"
	command_caves+="bash run_custom_server.sh $cluster_name Caves True^M"
else
	command_master+="bash run_custom_server.sh $cluster_name Master False^M"
	command_caves+="bash run_custom_server.sh $cluster_name Caves False^M"
fi

screen -S s -p 0 -X stuff "$commmand_master"
echo "starting master shard"
sleep 10
screen -S c -p 0 -X stuff "$commmand_caves"
echo "starting cave shard"
sleep 10
echo "both servers started"

