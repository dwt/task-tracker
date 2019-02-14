FROM ubuntu:18.04
LABEL maintainer="Dan Levin <dan@badpacket.in>, Martin Häcker <spamfaenger@gmx.de>"

ENV LC_ALL=C.UTF-8 LANG=C.UTF-8  

# How does docker figure out when to rerun these lines?
RUN apt-get update \
    && apt-get -y install curl gnupg2 python3-pip python3-dev python3-venv git \
    && apt-get -y install python2.7 pandoc
    # Required due to pandoc which is used by something installed by poetry :-/

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

EXPOSE 5000

# TODO These are also defined in docker-compose.yml - not sure where they should better be
ENV FLASK_DEBUG=1 FLASK_RUN_HOST=0.0.0.0
ENTRYPOINT poetry run flask run
