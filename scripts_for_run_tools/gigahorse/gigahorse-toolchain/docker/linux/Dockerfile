#FROM ubuntu:21.04
FROM ubuntu:focal
USER root

ENV DEBIAN_FRONTEND=noninteractive

# Install some essentials
RUN apt-get update && apt-get install -y \
    build-essential \
    libboost-all-dev \
    curl \
    libncurses5 \
    libtinfo5 \
    libffi-dev \
    libncurses5-dev \
    libsqlite3-dev \
    mcpp
#add by yyz

# Install python3
RUN apt-get install python3-dev python3-pip -y

# Install souffle
#RUN curl -s https://packagecloud.io/install/repositories/souffle-lang/souffle/script.deb.sh | bash
#RUN apt-get update && apt-get install souffle -y

# Dependencies for Gigahorse output viz
RUN apt-get update && apt-get install -y graphviz
RUN apt-get update && apt-get install -y libssl-dev

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install pydot

# Set up a non-root 'gigahorse' user
RUN groupadd -r gigahorse && useradd -ms /bin/bash -g gigahorse gigahorse

RUN mkdir -p /opt/gigahorse/gigahorse-toolchain

# Copy gigahorse project root
COPY . /opt/gigahorse/gigahorse-toolchain/

RUN chown -R gigahorse:gigahorse /opt/gigahorse
RUN chmod -R o+rwx /opt/gigahorse

# Install souffle by yyz souffle 2.0.2 version
RUN dpkg -i /opt/gigahorse/gigahorse-toolchain/my_folder/libffi6_3.2.1-8_amd64.deb
RUN dpkg -i /opt/gigahorse/gigahorse-toolchain/my_folder/souffle_2.0.2-1_amd64.deb

# Switch to new 'gigahorse' user context
USER gigahorse

# Souffle-addon bare-minimum make
RUN cd /opt/gigahorse/gigahorse-toolchain/souffle-addon && make libsoufflenum.so

#CMD ["-h"]
#ENTRYPOINT ["/opt/gigahorse/gigahorse-toolchain/gigahorse.py"]
