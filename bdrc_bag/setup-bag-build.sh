#!/usr/bin/env bash
#
# Prepare the development directory for building an executable archive
# See https://docs.python.org/3/library/zipapp.html
# Creating Standalone Applications with zipapp

export bagSync=bagSync

if [[ ! -d $bagSync ]]; then
    mkdir $bagSync
fi


python3 -m pip install -r requirements.txt --target $bagSync
#
# We don't want distInfos in target
find $bagSync -type d -name \*dist-info -exec rm -rf {} +