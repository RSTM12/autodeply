#!/bin/bash
set -e

echo "Starting TOR..."
tor -f /etc/tor/torrc &
TOR_PID=$!

echo "Waiting for TOR to be ready..."
for i in $(seq 1 30); do
    if nc -z 127.0.0.1 9050 2>/dev/null; then
        echo "TOR ready!"
        break
    fi
    echo "TOR not ready yet... ($i/30)"
    sleep 3
done

if ! nc -z 127.0.0.1 9050 2>/dev/null; then
    echo "WARNING: TOR failed to start, running without TOR"
fi

exec python bot.py
