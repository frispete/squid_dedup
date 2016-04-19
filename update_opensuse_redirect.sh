#!/bin/bash

./generate_openSUSE_redirects.py -v
cp -v opensuse-redirect.rules /etc/squid
/usr/sbin/squid -k reconfigure

