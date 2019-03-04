FROM ubuntu:18.04

LABEL maintainer="Dan Levin <dan@badpacket.in>, Martin Häcker <spamfaenger@gmx.de>"
LABEL description="This image is intended as a developent environment for task-tracker."

ENV LC_ALL=C.UTF-8 LANG=C.UTF-8  

RUN apt-get update \
    && apt-get -y install \
        python3.7 \
        python3-pip \
        python3-venv \
        curl \
        git \
        gnupg2

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get -y install yarn

WORKDIR /task-tracker
# for a more release-y image, this would be the right way to go. But it does slow down development
# so I copy just what is required for the build commands
# COPY . /task-tracker

# js dependencies
COPY package.json yarn.lock /task-tracker/
RUN yarn install
# TODO consider how much of this could be run on a different / dedicated container
# Later symlink /tmp/node_packages to wherever they are needed
# TODO How would I mount a volume to contain the download caches for yarn / pip to speed up image creation?

# py dependencies
COPY pyproject.toml poetry.lock /task-tracker/
RUN pip3 install poetry \
    && poetry run pip install --upgrade setuptools wheel pip \
    && poetry install

# TODO find a way to cache downloaded packages (os, python, yarn) so image rebuilds can use those caches
# maybe use VOLUME @see https://docs.docker.com/engine/reference/builder/#volume ?
# maybe use experimental --mount features 
# @see https://github.com/moby/buildkit/blob/master/frontend/dockerfile/docs/experimental.md
