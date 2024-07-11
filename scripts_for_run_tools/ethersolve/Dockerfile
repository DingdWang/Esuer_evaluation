#FROM python:3.8.10-slim-buster
#WORKDIR /app
#COPY while.py .
FROM  ubuntu:focal
COPY . /ethersolve_eva
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y openjdk-11-jdk python3 pip
#RUN apt-get install -y openjdk-11-jdk python3 pip
#RUN pip install -r ethersolve_eva/requirements.txt (不需要timeout_detect那个库）
#RUN apt-get -y install gcc
#RUN apt-get -y install openjdk-11-jdk