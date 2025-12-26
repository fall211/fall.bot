#!/usr/bin/bash

path="$HOME/.klei/"

if [ ! $1 ]
then
        echo "pass in parameters (world_folder beta(optional))"
        exit 1
fi

if [ $2 = "beta" ]
then
        path+="DoNotStarveTogetherBetaBranch/$1"
else
        path+="DoNotStarveTogether/$1"
fi

if [ ! -e "$path" ]
then
        echo "$path does not exist"
        exit 1
fi

gsutil -m cp -r $path gs://dst-server
