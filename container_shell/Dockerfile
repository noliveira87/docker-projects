FROM ubuntu:20.04

RUN apt-get update \
 && apt-get install -y sudo gnupg wget software-properties-common

RUN adduser --disabled-password --gecos '' docker
RUN adduser docker sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
WORKDIR /home/docker

USER docker

RUN wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
RUN echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.com/apt/ubuntu jammy/mongodb-enterprise/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-enterprise.list

RUN sudo add-apt-repository ppa:redislabs/redis

RUN sudo apt-get update
RUN sudo apt-get install -y mongodb-mongosh redis \
 && sudo apt-get clean autoclean \
 && sudo apt-get autoremove --yes \
 && sudo rm -rf /var/lib/{apt,dpkg,cache,log}/

RUN wget https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem

ENTRYPOINT ["tail", "-f", "/dev/null"]
