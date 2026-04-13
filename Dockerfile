FROM python:3.11-slim

RUN apt-get update && apt-get install -y tor netcat-openbsd && rm -rf /var/lib/apt/lists/*

RUN echo "ControlPort 9051" >> /etc/tor/torrc \
 && echo "CookieAuthentication 1" >> /etc/tor/torrc \
 && echo "SocksPort 9050" >> /etc/tor/torrc \
 && echo "Log notice stdout" >> /etc/tor/torrc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN echo '#!/bin/bash' > /app/start.sh \
 && echo 'echo "=== Starting TOR ==="' >> /app/start.sh \
 && echo 'tor -f /etc/tor/torrc &' >> /app/start.sh \
 && echo 'TOR_PID=$!' >> /app/start.sh \
 && echo 'sleep 20' >> /app/start.sh \
 && echo 'echo "=== TOR Status ==="' >> /app/start.sh \
 && echo 'if nc -z 127.0.0.1 9050 2>/dev/null; then' >> /app/start.sh \
 && echo '    echo "TOR ready! Port 9050 open"' >> /app/start.sh \
 && echo 'else' >> /app/start.sh \
 && echo '    echo "TOR FAILED: port 9050 not open"' >> /app/start.sh \
 && echo 'fi' >> /app/start.sh \
 && echo 'exec python bot.py' >> /app/start.sh \
 && chmod +x /app/start.sh

CMD ["/bin/bash", "/app/start.sh"]
