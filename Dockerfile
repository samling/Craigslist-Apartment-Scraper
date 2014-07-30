FROM samling/pythonbase

# Add pyapp
ADD pyapp/ /app

# Set permissions
RUN chown -R root /app

# Install BeautifulSoup
RUN apt-get install -y python-bs4

# Install requirements via pip
RUN pip install -r /app/requirements.txt

# Run script with python binary
CMD ["/usr/bin/python", "/app/cl-scrape.py"]

# Use this to simply run the script and exit; set up cronjob on docker host
#CMD ["/bin/bash", "/app/cl-scrape.sh"]

# Use this to set up cronjob inside container
# Kind of needs to be done this way or it can never check if the results are the same as last time
#CMD ["/bin/bash", "/app/startup.sh"]
