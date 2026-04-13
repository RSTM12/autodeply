FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tor \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN echo "ControlPort 9051" >> /etc/tor/torrc \
 && echo "CookieAuthentication 0" >> /etc/tor/torrc \
 && echo "HashedControlPassword \"\"" >> /etc/tor/torrc \
 && echo "SocksPort 9050" >> /etc/tor/torrc \
 && echo "Log notice stdout" >> /etc/tor/torrc \
 && echo "DataDirectory /var/lib/tor" >> /etc/tor/torrc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Starting TOR ==="
tor -f /etc/tor/torrc &

echo "=== Waiting for TOR (max 60s) ==="
for i in $(seq 1 30); do
    if nc -z 127.0.0.1 9050 2>/dev/null; then
        echo "TOR ready! Port 9050 open"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo "=== Starting Bot ==="
exec python bot.py
EOF

RUN chmod +x /app/start.sh

CMD ["/bin/bash", "/app/start.sh"]
