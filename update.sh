#!/bin/bash
cd /home/Tamik327/back-vits || exit 1
git fetch origin
git reset --hard origin/master
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
