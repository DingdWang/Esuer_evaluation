FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y \
    python3-dev \
    python3-pip

RUN \
  pip3 install --upgrade pip

COPY . /vandal

RUN  pip install -r vandal/vandal/requirements.txt



