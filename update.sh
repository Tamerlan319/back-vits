#!/bin/bash
chmod +x "$0"
cd /home/Tamik327/back-vits || exit 1

# Остановка старых процессов
pkill -f "python manage.py"

# Обновление кода
git fetch origin
git reset --hard origin/master

# Перезагрузка приложения
curl -X POST \
  "https://www.pythonanywhere.com/api/v0/user/Tamik327/webapps/tamik327.pythonanywhere.com/reload/" \
  -H "Authorization: Token 5a5357fa9b3cd839874fb47b3c4a65c86b619b36"