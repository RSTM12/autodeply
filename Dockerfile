FROM python:3.11-slim

RUN apt-get update && apt-get install -y tor curl && rm -rf /var/lib/apt/lists/*

RUN echo "ControlPort 9051" >> /etc/tor/torrc \
 && echo "CookieAuthentication 1" >> /etc/tor/torrc \
 && echo "SocksPort 9050" >> /etc/tor/torrc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Buat startup script
RUN echo '#!/bin/bash\n\
tor -f /etc/tor/torrc &\n\
echo "Waiting for TOR to bootstrap..."\n\
for i in $(seq 1 30); do\n\
    if curl -s --socks5 127.0.0.1:9050 --max-time 5 https://check.torproject.org/ > /dev/null 2>&1; then\n\
        echo "TOR is ready!"\n\
        break\n\
    fi\n\
    echo "TOR not ready yet... ($i/30)"\n\
    sleep 3\n\
done\n\
python bot.py' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
