#!/bin/bash

WORKSPACE_NAME=ssc_podcast

# setup for virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
export PROJECT_HOME=$HOME
source /usr/local/bin/virtualenvwrapper.sh

# activate workspace
workon $WORKSPACE_NAME

# get script location (from argument)
SCRIPT_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPT_HOME

# run scripts
source aws_access.sh
python ssc_podcast.py

if [ $? -eq 0 ]
then
  # add and push to git
  cd ..
  git add .
  git commit -m 'updating podcasts'
  git push origin master
fi

# deactivate workspace
deactivate
