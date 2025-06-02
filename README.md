# CasinoUp

Онлайн казино с различными мини-играми, включая:
- Slots (Слоты)
- Dice (Кости)
- Coinflip (Монетка)
- Miner (Сапёр)
- Valb1k Coin (Кликер)

## Технологии

- Python 3.9+
- Flask
- SQLAlchemy
- Bootstrap 5
- PostgreSQL

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Archuqq/casinoup.git
cd casinoup
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
pip install -r requirements.txt
```

3. Создайте файл `.env` и настройте переменные окружения:
```
FLASK_APP=wsgi.py
FLASK_ENV=development
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key
```

4. Инициализируйте базу данных:
```bash
flask db upgrade
```

5. Запустите приложение:
```bash
flask run
```

## Деплой

Проект готов к деплою на Railway. Необходимые файлы:
- Procfile
- requirements.txt
- wsgi.py

## Лицензия

MIT 