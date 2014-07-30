FROM samling/pythonbase

# Add pyapp
ADD pyapp/ /app

# Set permissions
RUN chown -R root /app

# Install cron, nano, screen for scheduled execution of script via cronjob
#RUN apt-get install -y cron nano screen

# Set up cron
#RUN crontab /app/cron.conf

# To keep cron running, we'll run apache in the foreground so the container doesn't exit
#RUN apt-get install -y apache2

# Set up apache environment variables
#ENV APACHE_LOCK_DIR /var/lock
#ENV APACHE_RUN_USER www-data
#ENV APACHE_RUN_GROUP www-data
#ENV APACHE_LOG_DIR /var/log/apache2/
#ENV APACHE_PID_FILE /var/apache.pid

# Install BeautifulSoup
RUN apt-get install -y python-bs4

# Install requirements via pip
RUN pip install -r /app/requirements.txt

# Use this to simply run the script and exit; set up cronjob on docker host
CMD ["/bin/bash", "/app/cl-scrape.sh"]

# Use this to set up cronjob inside container
# Kind of needs to be done this way or it can never check if the results are the same as last time
#CMD ["/bin/bash", "/app/startup.sh"]
