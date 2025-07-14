#!/bin/bash

if [ -d "/app/ssl" ]; then
    echo "[PyServe] Fixing SSL files permissions..."
    
    sudo chown -R pyserve:pyserve /app/ssl
    
    sudo chmod 755 /app/ssl
    if [ -f "/app/ssl/privkey.pem" ]; then
        sudo chmod 600 /app/ssl/privkey.pem
        sudo chown pyserve:pyserve /app/ssl/privkey.pem
    fi
    if [ -f "/app/ssl/fullchain.pem" ]; then
        sudo chmod 644 /app/ssl/fullchain.pem
        sudo chown pyserve:pyserve /app/ssl/fullchain.pem
    fi

    if [ -f "/app/ssl/cert.pem" ]; then
        sudo chmod 644 /app/ssl/cert.pem
        sudo chown pyserve:pyserve /app/ssl/cert.pem
    fi
    if [ -f "/app/ssl/key.pem" ]; then
        sudo chmod 600 /app/ssl/key.pem
        sudo chown pyserve:pyserve /app/ssl/key.pem
    fi
    
    echo "[PyServe] SSL files permissions fixed"
fi

exec "$@"
