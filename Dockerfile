FROM python:3.11-slim

RUN apt-get update && apt-get install -y tor netcat-openbsd && rm -rf /var/lib/apt/lists/*

RUN echo "ControlPort 9051" >> /etc/tor/torrc \
 && echo "CookieAuthentication 1" >> /etc/tor/torrc \
 && echo "SocksPort 9050" >> /etc/tor/torrc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN printf '#!/bin/bash\n\
set -e\n\
echo "Starting TOR..."\n\
tor -f /etc/tor/torrc &\n\
echo "Waiting for TOR to be ready..."\n\
for i in $(seq 1 30); do\n\
    if nc -z 127.0.0.1 9050 2>/dev/null; then\n\
        echo "TOR ready!"\n\
        break\n\
    fi\n\
    echo "TOR not ready yet... ($i/30)"\n\
    sleep 3\n\
done\n\
if ! nc -z 127.0.0.1 9050 2>/dev/null; then\n\
    echo "WARNING: TOR failed to start, running without TOR"\n\
fi\n\
exec python bot.py\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/bin/bash", "/app/start.sh"]
