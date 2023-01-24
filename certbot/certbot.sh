#!/bin/sh

certbot certonly -d pi-humidity.webredirect.org --email hayden.dorahy@gmail.com --agree-tos --standalone --non-interactive
chmod -R 777 /etc/letsencrypt
