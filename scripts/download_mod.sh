#!/usr/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <MOD_ID> <PATH>"
    exit 1
fi

MOD_ID=$1
DOWNLOAD_PATH=$2
DST_APP_ID=322330

steamcmd +force_install_dir $DOWNLOAD_PATH +login anonymous +workshop_download_item $DST_APP_ID $MOD_ID +quit