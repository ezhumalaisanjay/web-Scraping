#!/bin/bash

# Update packages
yum update -y

# Install Python 3.10
amazon-linux-extras install python3.10 -y
yum install python3.10-pip -y

# Create symbolic links
ln -sf /usr/bin/python3.10 /usr/bin/python3
ln -sf /usr/bin/pip3.10 /usr/bin/pip3

# Install global packages
pip3 install --upgrade pip
pip3 install virtualenv

# Create app directory
mkdir -p /var/www/html/linkedin-scraper