FROM ubuntu:18.04
MAINTAINER Dan Levin <dan@badpacket.in>

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8  

WORKDIR /task-tracker

RUN apt-get update && apt-get -y install curl gnupg2 python3-pip python3-dev python3-venv

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get -y install yarn
# Move these into the build process once the problems described in the entrypoint can be resolved.
#   && pip3 install -r requirements.txt \
#   && poetry install \
#   && yarn isntall

# Required due to pandoc which is used by something installed by poetry :-/
RUN apt-get -y install python2.7 pandoc
