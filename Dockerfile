FROM python:3.12-alpine

RUN mkdir /src /data
COPY src/*  /src
RUN pip install -r /src/requirements.txt
RUN echo '0  *  *  *  *   cd / && /usr/local/bin/python3.12 /src/scrape.py' > /etc/crontabs/root

# running once on boot so I don't have to wait every hour to test things :)
RUN echo '@reboot  cd / && /usr/local/bin/python3.12 /src/scrape.py' >> /etc/crontabs/root

# Bad practice to (cron) to fork another process (python) in the same container.
# Cron is usually run on a host server, but this allows us to run the application locally.
CMD  ["crond", "-f"]