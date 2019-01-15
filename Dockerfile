FROM ubuntu:18.04
MAINTAINER Dan Levin <dan@badpacket.in>

COPY ./requirements.txt /task-tracker/

WORKDIR /task-tracker

RUN apt-get update && apt-get -y install curl gnupg2 python3-pip python3-dev python3-venv

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get -y install yarn \
    && pip3 install -r requirements.txt

