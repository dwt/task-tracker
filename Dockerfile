FROM ubuntu:18.04
MAINTAINER Dan Levin <dan@badpacket.in>

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8  

RUN apt-get update && apt-get -y install curl gnupg2 python3-pip python3-dev python3-venv git

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get -y install yarn

# Required due to pandoc which is used by something installed by poetry :-/
RUN apt-get -y install python2.7 pandoc

WORKDIR /task-tracker

# seems like I would want to manually copy the lock file to ensure that this step gets rerun when the lock file changes?
RUN yarn install

# seems like I would want to manually copy in the requirements.txt, pyproject.toml and poetry.lock files
# to ensure these steps get rerun when those files change?
RUN pip3 install --no-cache-dir --upgrade setuptools wheel pip
RUN /bin/bash
  # \
  #   && pip install --no-cache-dir --requirement requirements.txt \
  #   && poetry config settings.virtualenvs.create false \
  #   && poetry install
#    && pip uninstall --yes poetry

EXPOSE 5000

# RUN ["flask" "run"]
