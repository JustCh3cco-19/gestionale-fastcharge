#!/bin/bash

# Make sure that we are in the right directory
if [ ! -f Dockerfile ]; then
    echo "Error: Either Dockerfile is missing in the current directory."
    exit 1
fi

# Sudo is typically not required on Mac OS
if [[ $(uname) == "Darwin" ]]; then
    docker build . -t gestionale-frontend
else
    sudo docker build . -t gestionale-frontend
fi