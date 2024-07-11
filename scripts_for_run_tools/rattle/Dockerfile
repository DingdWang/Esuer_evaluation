#FROM ubuntu:focal
FROM ubuntu:bionic
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y \
    python3-dev \
    python3-pip \
    python3.8

RUN \
  pip3 install --upgrade pip

COPY . /rattle

RUN  pip install -r rattle/rattle/requirements.txt



