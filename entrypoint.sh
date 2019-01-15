#!/bin/bash


####
# These should actually be done at container-build time, but are difficult to
# encapsulate (while also supporing volumes) given the current project
# structure layout.
pyvenv .
source bin/activate
pip install -r requirements.txt
poetry install
yarn install
####

flask run
