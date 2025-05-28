# Backend для VITS (Virtual IT School)

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.1-green.svg)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)](https://www.django-rest-framework.org)

Backend часть образовательной платформы VITS с REST API на Django.

## 🚀 Быстрый старт

### Предварительные требования
- Python 3.10+
- PostgreSQL 12+ (или SQLite для разработки)
- Redis (для кеширования)

### Установка
```bash
# Клонировать репозиторий
git clone https://github.com/Tamerlan319/back-vits.git
cd back-vits

# Создать и активировать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# или venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
