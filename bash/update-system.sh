#!/usr/bin/env bash
# For Updating Packages and Portainer
# Tested on Ubuntu 20.04

LATEST="$(wget -qO- https://hub.docker.com/v1/repositories/portainer/portainer-ce/tags)"
LATEST=$(echo $LATEST | sed "s/{//g" | sed "s/}//g" | sed "s/\"//g" | cut -d ' ' -f2)
RUNNING=$(docker inspect "portainer/portainer-ce" | grep Id | sed "s/\"//g" | sed "s/,//g" | tr -s ' ' | cut -d ' ' -f3)
if [ "$RUNNING" != "$LATEST" ]; then
    docker stop portainer && docker rm portainer && docker rmi portainer/portainer-ce &&
        docker run -d -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -e VIRTUAL_HOST=portainer.home -e VIRTUAL_PORT=9000 -v portainer_data:/data --network net portainer/portainer-ce:latest
fi
sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y
