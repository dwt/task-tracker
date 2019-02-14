FROM ubuntu:18.04

LABEL maintainer="Dan Levin <dan@badpacket.in>, Martin Häcker <spamfaenger@gmx.de>"
LABEL description="This image is intended as a developent environment for task-tracker."

ENV LC_ALL=C.UTF-8 LANG=C.UTF-8  

# How does docker figure out when to rerun these lines?
# FIXME according to https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#leverage-build-cache
# The cache for this RUN action is only invalidated if the line changes. So how do I ensure to either get updates regularly
# or force the build process to respect some minimum or pinned versions of packages?
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

# JS dependencies
COPY package.json yarn.lock /tmp/
RUN cd /tmp && yarn install
# TODO consider how much of this could be run on a different / dedicated container
# Later symlink /tmp/node_packages to wherever they are needed
# TODO How would I mount a volume to contain the download caches for yarn / pip to speed up image creation?

# py dependencies
COPY pyproject.toml poetry.lock /tmp/
RUN pip3 install poetry \
    && cd /tmp \
    && poetry run pip install --upgrade setuptools wheel pip \
    && poetry install

# running stuff
# TODO These are also defined in docker-compose.yml - not sure where they should better be
EXPOSE 5000
ENV FLASK_DEBUG=1 FLASK_RUN_HOST=0.0.0.0
VOLUME /task-tracker
# TODSO does it make sense to declare these here?
# ENTRYPOINT poetry run
# CMD flask run


# TODO find a way to cache downloaded packages (os, python, yarn) so image rebuilds can use those caches
# maybe use VOLUME @see https://docs.docker.com/engine/reference/builder/#volume ?
# maybe use experimental --mount features 
# @see https://github.com/moby/buildkit/blob/master/frontend/dockerfile/docs/experimental.md
