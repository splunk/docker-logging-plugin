#!/usr/bin/env bash

printf "\nUpdate apt-get linux packages to latest\n"
sudo apt-get update -y

printf "\nInstall pre-requirements\n"
sudo apt-get install \
    apt-transport-https -y\
    ca-certificates -y\
    curl -y\
    software-properties-common

printf "\nDownload and Add docker PGP public key\n"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

printf "\nAdding docker repository tp find package\n"
sudo add-apt-repository -y\
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

printf "\nInstalling docker\n"
sudo apt-get update -y
sudo apt-get install docker-ce -y
sudo usermod -a -G docker ubuntu
sudo apt-get install make -y


printf "\nClone docker-logging-plugin repo\n"
git clone https://github.com/splunk/docker-logging-plugin.git
cd docker-logging-plugin
git checkout develop

printf "\nBuild and enable docker logging plugin\n"
sudo make
sudo make enable
