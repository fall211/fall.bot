##!/usr/bin/bash

#64-bit dependencies
sudo apt-get install libstdc++6:i386 libgcc1:i386 libcurl4-gnutls-dev:i386

#steamcmd
mkdir -p $HOME/steamcmd/
cd $HOME/steamcmd/
wget "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"
tar -xvzf steamcmd_linux.tar.gz
rm steamcmd_linux.tar.gz

mkdir -p $HOME/.klei/DoNotStarveTogether/
cd $HOME/.klei/DoNotStarveTogether/
cp -r $HOME/fall.bot/Templates/DST/Template .