<p align="center">
  <a href="https://github.com/ivanyuk-vl/foodgram-project-react"><img alt="GitHub Actions status" src="https://github.com/ivanyuk-vl/foodgram-project-react/workflows/foodgram workflow/badge.svg"></a>
</p>

# Продуктовый помощник
## Описание
Cайт на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд. 
## Технологии
- django 2.2.16
- django-cleanup 6.0.0
- django-filter 2.4.0
- djangorestframework 3.12.4
- djoser 2.1.0
- gunicorn 20.0.4
- Pillow 9.1.1
- psycopg2-binary 2.8.6
- python-dotenv 0.20.0
- reportlab 3.6.10
### Команда для клонирования репозитория
```
git clone git@github.com:ivanyuk-vl/foodgram-project-react.git
```
## Запуск проекта
### Установить Docker Compose
```
https://docs.docker.com/compose/install/
```
### Запуск приложения в контейнерах
- Cоздать папку для проекта
- Cоздать в папке проекта файл docker-compose.yml по шаблону:
```
version: '3.3'
services:
  frontend:
    image: foodgram_frontend
    volumes:
      - frontend_volume:/app/result_build/
  db:
    image: postgres:13.0-alpine
    restart: always
    volumes:
      - /var/lib/postgresql/data/
    env_file:
      - ./.env
  web:
    image: foodgram_backend
    restart: always
    volumes:
      - static_volume:/app/static_/
      - media_volume:/app/media/
    depends_on:
      - db
    env_file:
      - ./.env
  nginx:
    image: nginx:1.19.3
    restart: always
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - frontend_volume:/usr/share/nginx/html/
      - static_volume:/var/html/static_/
      - media_volume:/var/html/media/
    depends_on:
      - frontend
      - web
volumes:
  frontend_volume:
  static_volume:
  media_volume:
```
- Выполнить следующие команды в терминале:
```
cd <путь_до_папки_с_склонированным_репозиторием>/frontend/
docker build -t foodgram_frontend .
cd ../backend/foodgram_api/
docker build -t foodgram_backend .
cd <путь_до_папки_с_проектом>
cp <путь_до_папки_с_склонированным_репозиторием>/infra/nginx.conf .
```
- Cоздать в папке с проектом файл .env по шаблону:
```
SECRET_KEY=<секретный ключ>
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```
- Выполнить следующие команды в терминале:
```
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --no-input
```
- Команда для создания супер-пользователя:
```
docker compose exec web python manage.py createsuperuser
```
- Команда для добавления списка ингредиентов в базу данных:
```
docker compose exec web python manage.py fill_ingredients
```
## Автор
https://github.com/ivanyuk-vl
### Проект, развернутый на сервере
- http://51.250.104.154/
- [документация](http://51.250.104.154/api/docs/)
- [админка](http://51.250.104.154/admin/)
