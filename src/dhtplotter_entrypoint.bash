#!/bin/bash

# Save the environment variables to a file that can be read by cron, as cron runs jobs in its own environment
# See this SO Q/A: https://stackoverflow.com/questions/27771781/how-can-i-access-docker-set-environment-variables-from-a-cron-job
printenv | grep -v \"no_proxy\" >> /etc/environment


# Specify exact path to python for cron, as it doesn't use it by default
# Renew the SSL certificate every Sunday at 0230
echo '30 2 * * 0 /usr/local/bin/python3 /src/my_certbot.py >> /var/log/cron.log 2>&1' > /tmp/my_cron
# Generate static images of the graphs every 10 minutes
echo '*/10 * * * * /usr/local/bin/python3 /src/dhtPlotterStatic.py' > /tmp/my_cron
crontab /tmp/my_cron
rm /tmp/my_cron
cron

python /src/my_certbot.py >> /var/log/cron.log 2>&1
python /src/dhtPlotterStatic.py
python /src/webserver.py
