FROM python:3.11-slim

RUN apt-get update && apt-get install -y tor netcat-openbsd && rm -rf /var/lib/apt/lists/*

RUN echo "ControlPort 9051" >> /etc/tor/torrc \
 && echo "CookieAuthentication 1" >> /etc/tor/torrc \
 && echo "SocksPort 9050" >> /etc/tor/torrc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x /app/start.sh

CMD ["/bin/bash", "/app/start.sh"]
