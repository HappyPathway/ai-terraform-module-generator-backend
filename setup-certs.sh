#!/bin/bash
set -e

# Create directories if they don't exist
mkdir -p nginx/certs

# Generate SSL certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/registry.local.key \
  -out nginx/certs/registry.local.crt \
  -subj "/CN=registry.local" \
  -addext "subjectAltName=DNS:registry.local"

# Set permissions
chmod 644 nginx/certs/registry.local.crt
chmod 600 nginx/certs/registry.local.key

echo "SSL certificate generated successfully"
echo "Add the following line to your /etc/hosts file:"
echo "127.0.0.1 registry.local"