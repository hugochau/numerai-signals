FROM --platform=$BUILDPLATFORM ubuntu:latest AS build
# FROM amd64/ubuntu:latest

ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "I am running on $BUILDPLATFORM, building for $TARGETPLATFORM" > /log

## for apt to be noninteractive
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true

RUN apt-get update -y 
RUN apt-get install -y\
    vim make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
    libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev openssl libssl-dev \
    git

RUN rm -rf ~/.pyenv
RUN curl https://pyenv.run | bash

RUN echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
RUN echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
RUN echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

RUN . /root/.bashrc && pyenv install 3.7.13
RUN . /root/.bashrc && pyenv global 3.7.13

# RUN . /root/.bashrc && pip install pipenv

RUN echo 'alias python="python3"' >> ~/.bashrc
RUN echo 'alias pip="pip3"' >> ~/.bashrc

COPY ./requirements.txt /
RUN . /root/.bashrc && pip install -r requirements.txt
