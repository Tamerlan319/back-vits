#!/bin/bash

# Копируем конфиг Gunicorn
sudo cp /root/back-vits/deploy/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# Копируем конфиг Nginx
sudo cp /root/back-vits/deploy/nginx.conf /etc/nginx/sites-available/vits44.ru
sudo ln -sf /etc/nginx/sites-available/vits44.ru /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

echo "Deployment configuration applied successfully!"