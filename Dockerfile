FROM python:3.11-slim

# Install TOR
RUN apt-get update && apt-get install -y tor && rm -rf /var/lib/apt/lists/*

# Config TOR: enable control port untuk rotate circuit
RUN echo "ControlPort 9051" >> /etc/tor/torrc \
 && echo "HashedControlPassword " >> /etc/tor/torrc \
 && echo "CookieAuthentication 1" >> /etc/tor/torrc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start TOR dulu, lalu jalankan bot
CMD tor -f /etc/tor/torrc & sleep 5 && python bot.py
