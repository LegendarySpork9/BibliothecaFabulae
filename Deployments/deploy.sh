#!/bin/bash
set -e

echo "=== BibliothecaFabulae Deployment ==="
echo ""

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo "Install it: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "Error: Docker Compose is not installed."
    exit 1
fi

# Generate .env if it doesn't exist
if [ ! -f .env ]; then
    echo "First-time setup — generating configuration..."
    echo ""

    SECRET_KEY=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 32)

    read -p "Domain name (e.g. fics.example.com, or leave blank for IP access): " DOMAIN
    DOMAIN=${DOMAIN:-localhost}

    read -p "Storage path inside container (default: /app/storage): " STORAGE_PATH
    STORAGE_PATH=${STORAGE_PATH:-/app/storage}

    cat > .env <<EOF
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
DATABASE_URL=sqlite+aiosqlite:///./data/bibliothecafabulae.db
CORS_ORIGINS=["https://${DOMAIN}","http://${DOMAIN}"]
ENVIRONMENT=production
LOG_DIR=./logs
EOF

    echo ".env created."
    echo ""
fi

# Generate self-signed SSL cert if none exists
if [ ! -f nginx/ssl/cert.pem ]; then
    echo "No SSL certificate found — generating a self-signed certificate."
    echo "Replace nginx/ssl/cert.pem and key.pem with real certificates for production."
    echo ""

    mkdir -p nginx/ssl

    openssl req -x509 -nodes -days 365 \
        -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/CN=${DOMAIN:-localhost}" \
        2>/dev/null

    echo "Self-signed certificate generated."
    echo ""
fi

# Build and start
echo "Building and starting containers..."
docker compose up -d --build

echo ""
echo "=== Deployment complete ==="
echo ""
echo "The application is running at:"
echo "  https://${DOMAIN:-localhost}"
echo ""
echo "Next steps:"
echo "  1. Open the URL above to run the setup wizard"
echo "  2. Replace nginx/ssl/ certs with real ones (Cloudflare Origin CA, Let's Encrypt, etc.)"
echo "  3. Run 'docker compose logs -f' to watch logs"
echo "  4. Run 'docker compose down' to stop"
echo "  5. Run 'docker compose up -d --build' to update after a git pull"
