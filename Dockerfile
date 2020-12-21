#syntax=docker/dockerfile:1.2
# Need to set `DOCKER_BUILDKIT=1` to build this

FROM ubuntu:20.04

LABEL maintainer="Dan Levin <dan@badpacket.in>, Martin Häcker <spamfaenger@gmx.de>"
LABEL description="This image is intended as a developent environment for task-tracker."

ENV LC_ALL=C.UTF-8 LANG=C.UTF-8

# Configure timezone, so the build doesn't hang on package installation asking for the timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,target=/var/cache/apt --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y \
    python3.7 \
    python3-pip \
    python3-venv \
    curl \
    git \
    gnupg2

RUN --mount=type=cache,target=/var/cache/apt --mount=type=cache,target=/var/lib/apt \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt-get update && apt-get install -y \
    yarn

# FIXME Change user to non root

WORKDIR /task-tracker
# for a more release-y image, this would be the right way to go. But it does slow down development
# so I copy just what is required for the build commands
# COPY . /task-tracker

# js dependencies
COPY package.json yarn.lock /task-tracker/
RUN --mount=type=cache,target=/usr/local/share/.cache/yarn/ \
    yarn install
# TODO consider how much of this could be run on a different / dedicated container
# Later symlink /tmp/node_packages to wherever they are needed
# TODO How would I mount a volume to contain the download caches for yarn / pip to speed up image creation?
# TODO consider how I would update the lock file? Some clever use of docker cp perhaps?

# py dependencies
COPY pyproject.toml poetry.lock /task-tracker/
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=cache,target=/root/.cache/pypoetry \
    pip3 install poetry \
    && poetry run pip install --upgrade setuptools wheel pip \
    && poetry install
