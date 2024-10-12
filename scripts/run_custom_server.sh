#!/usr/bin/bash

steamcmd_dir="$HOME/steamcmd"
install_dir="$HOME/dontstarvetogether_dedicated_server"
cluster_name="$1"
dontstarve_dir="$HOME/.klei/DoNotStarveTogether"

if [ $3 = "True" ]
then
	dontstarve_dir+="BetaBranch"
fi

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

cd "$steamcmd_dir" || fail "Missing $steamcmd_dir directory"

check_for_file "steamcmd.sh"
check_for_file "$dontstarve_dir/$cluster_name/cluster.ini"
check_for_file "$dontstarve_dir/$cluster_name/cluster_token.txt"
check_for_file "$dontstarve_dir/$cluster_name/Master/server.ini"
check_for_file "$dontstarve_dir/$cluster_name/Caves/server.ini"

if [ $3 = "True" ]
then
	./steamcmd.sh +force_install_dir "$install_dir" +login anonymous +app_update 343050 -beta updatebeta +quit
else
	./steamcmd.sh +force_install_dir "$install_dir" +login anonymous +app_update 343050 -beta public +quit
fi

check_for_file "$install_dir/bin64"

cd "$install_dir/bin64" || fail

run_shared=(./dontstarve_dedicated_server_nullrenderer_x64)
run_shared+=(-cluster "$cluster_name")
run_shared+=(-monitor_parent_process $$)

if [ $2 = "Caves"]
then
	"${run_shared[@]}" -shard Caves | sed 's/^/Caves:  /'
else
 	"${run_shared[@]}" -shard Master | sed 's/^/Master: /'
fi

	