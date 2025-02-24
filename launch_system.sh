#!/bin/bash

bash build-docker-images.sh

# Sudo is typically not required on Mac OS
if [[ $(uname) == "Darwin" ]]; then
    docker-compose up
    docker-compose down 
else
    sudo docker-compose up 
    # Removed docker-compose down because, after checking the right eth interface and ip address,
    # Linux runs always the first command and there is no chance that it arrives to docker-compose down
    # To fix that I added this command into systemd service 
    sudo docker-compose down
fi