#!/usr/bin/bash

# run this script from python script
# steps to automate making new dst worlds
# 1. create a discord bot command
#     1. this should take in parameters for cluster name, branch, type(Newbie/main)
#     2. also should download the cluster.zip to the vm
# 2. run bash from python
# 3. checks validity of the cluster.zip
# 4. makes new folder from Template cluster in the desired branch
# 5. copies master and cave save files to the cluster
# 6. renames appropriate leveldataoverride 
# 7. deletes zip file
# 8. optional: set options for mods, server name, description, pvp, etc

# check validity of the parameters (cluster name, branch, type)
if [ $# -ne 3 ]; then
    echo "Usage: $0 <cluster_name> <main/beta> <main/relaxed>"
    exit 1
fi

CLUSTER_NAME=$1
BRANCH=$2
TYPE=$3

# check if cluster.zip exists
if [ ! -f cluster.zip ]; then
    echo "cluster.zip does not exist"
    exit 1
fi

# Unzip cluster.zip to a temp folder
unzip -o -q cluster.zip -d $HOME/fall.bot/temp

# Get the name of the first folder inside the temp directory, ignoring __MACOSX
first_folder=$(ls -1 $HOME/fall.bot/temp | grep -v "__MACOSX" | head -n 1)

Check if the required directories exist
if [ ! -d "$HOME/fall.bot/temp/$first_folder/Master/save" ] || [ ! -d "$HOME/fall.bot/temp/$first_folder/Caves/save" ]; then
    echo "cluster.zip is not valid"
    rm -rf $HOME/fall.bot/temp
    rm cluster.zip
    exit 1
fi


# check if cluster name already exists
if [ -d "$HOME/.klei/DoNotStarveTogether/$CLUSTER_NAME" ] || [ -d "$HOME/.klei/DoNotStarveTogetherBetaBranch/$CLUSTER_NAME" ]; then
    echo "cluster name already exists"
    rm -rf $HOME/fall.bot/temp
    rm cluster.zip
    exit 1
fi

# check if branch is valid
if [ $BRANCH != "main" ] && [ $BRANCH != "beta" ]; then
    echo "branch is not valid, enter main/beta"
    rm -rf $HOME/fall.bot/temp
    rm cluster.zip
    exit 1
fi

# check if type is valid
if [ $TYPE != "main" ] && [ $TYPE != "relaxed" ]; then
    echo "type is not valid, enter main/relaxed"
    rm -rf $HOME/fall.bot/temp
    rm cluster.zip
    exit 1
fi

# make new folder from Template cluster in the desired branch
DEST_PATH="$HOME/.klei/"
if [ $BRANCH == "main" ]; then
    DEST_PATH+="DoNotStarveTogether/"
else
    DEST_PATH+="DoNotStarveTogetherBetaBranch/"
fi

cp -r $HOME/.klei/DoNotStarveTogether/Template $DEST_PATH$CLUSTER_NAME
cp -r $HOME/fall.bot/temp/$first_folder/Master/save $DEST_PATH$CLUSTER_NAME/Master
cp -r $HOME/fall.bot/temp/$first_folder/Caves/save $DEST_PATH$CLUSTER_NAME/Caves

# rename appropriate leveldataoverride
if [ $TYPE == "main" ]; then
    mv $DEST_PATH$CLUSTER_NAME/Master/leveldataoverrideMAIN.lua $DEST_PATH$CLUSTER_NAME/Master/leveldataoverride.lua
else
    mv $DEST_PATH$CLUSTER_NAME/Master/leveldataoverrideNOOBS.lua $DEST_PATH$CLUSTER_NAME/Master/leveldataoverride.lua
fi

# delete temp folder and cluster.zip
rm -rf $HOME/fall.bot/temp
rm cluster.zip
exit 0