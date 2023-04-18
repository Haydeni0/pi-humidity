#!/bin/bash

# Save the environment variables to a file that can be read by cron, as cron runs jobs in its own environment
# See this SO Q/A: https://stackoverflow.com/questions/27771781/how-can-i-access-docker-set-environment-variables-from-a-cron-job
printenv | grep -v \"no_proxy\" >> /etc/environment

# Set up a cronjob to renew the certificate every Sunday at 0230
# This completely overrides all other cronjobs - shouldn't be a problem as this is running in a container
# Specify exact path to python for cron
echo '30 2 * * 0 /usr/local/bin/python3 /src/my_certbot.py >> /var/log/cron.log 2>&1' >> /tmp/my_cron
crontab /tmp/my_cron
rm /tmp/my_cron
cron

python /src/my_certbot.py >> /var/log/cron.log 2>&1
python /src/webserver.py
