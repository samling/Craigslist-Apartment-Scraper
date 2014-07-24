# Start cron service in background without upstart
cron -f &

# Generate config file from environment variables
/usr/bin/python /app/buildcfg.py

# Run the python script once to kick things off
/bin/bash /app/cl-scrape.sh

# Start apache in the foreground so the docker container doesn't exit
/usr/sbin/apache2 -D FOREGROUND
