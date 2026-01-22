#!/bin/bash
# KIKI Engine Bitnami LAMP Setup Script
set -e

# Update and install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv golang-go redis-server docker.io docker-compose

# Python virtual environment for Flask
cd /opt/bitnami/projects/kiki-agent/web
python3 -m venv venv
source venv/bin/activate
pip install flask

deactivate

# Build Go binary (if needed)
cd /opt/bitnami/projects/kiki-agent/go-engine
go build -o syncflow main.go

# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Systemd unit for Go service (example)
echo "[Unit]
Description=KIKI Go Engine
After=network.target redis-server.service

[Service]
WorkingDirectory=/opt/bitnami/projects/kiki-agent/go-engine
ExecStart=/opt/bitnami/projects/kiki-agent/go-engine/syncflow
Restart=always
User=bitnami

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/kiki-go-engine.service

sudo systemctl daemon-reload
sudo systemctl enable kiki-go-engine

# Systemd unit for Flask (example)
echo "[Unit]
Description=KIKI Flask Web
After=network.target

[Service]
WorkingDirectory=/opt/bitnami/projects/kiki-agent/web
ExecStart=/opt/bitnami/projects/kiki-agent/web/venv/bin/python app.py
Restart=always
User=bitnami

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/kiki-web.service

sudo systemctl daemon-reload
sudo systemctl enable kiki-web

# Print completion message
echo "KIKI Engine Bitnami setup complete. Use 'docker-compose up -d' to start containers."
