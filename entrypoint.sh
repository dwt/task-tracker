#!/bin/bash


####
# There's an argument to be made that virtualenv isn't necessary and shouldn't
# be used in docker
pyvenv . 
source bin/activate
# These should actually be done at container-build time, but are difficult to
# encapsulate (while also supporing volumes) given the current project
# structure layout.
pip install -r requirements.txt
poetry install
yarn install
####

flask run
