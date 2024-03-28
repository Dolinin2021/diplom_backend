# Дипломный проект: Облачное хранилище (серверная часть)

## Описание
Серверная часть облачного хранилища.

## Функциональность

### Административный интерфейс системы
* Регистрация пользователя
* Получение списка пользователей
* Удаление пользователя
* Аутентификация пользователя

### Интерфейс управления файловым хранилищем.
* Получение списка файлов пользователя
* Загрузка файла в хранилище
* Удаление файла из хранилища
* Переименование файла
* Изменение комментария к файлу
* Формирование специальной ссылки на файл для использования внешними пользователями или веб-приложениями

## Настройка и запуск проекта
```
# генерируем ssh-ключ
ssh-keygen -t ed25519

# выводим содержимое публичного ключа в консоль
cat ~/.ssh/id_ed25519.pub

# копируем ssh-ключ

# Создаём сервер на reg.ru, добавляем ssh-ключ, добавляем сервер

# Получаем учётные данные на электронную почту

# В терминале через ssh подключаемся к серверу, вводим пароль
ssh root@79.174.91.160

# если есть пароль, вводим его. Добавляем пользователя
adduser ilya

# делаем пользователя суперпользователем
usermod ilya -aG sudo

# выходим и заходим с пользователя ilya
exit
ssh ilya@79.174.91.160

# переходим в домашнюю директорию
cd ~

# обновляем список доступных пакетов ПО
sudo apt update

# устанавливаем необходимое ПО
sudo apt install python3-venv python3-pip postgresql nginx
sudo systemctl start nginx
sudo systemctl status nginx

# клонируем бэкенд
git --version
git clone https://github.com/Dolinin2021/diplom_backend/
ls
cd diplom_backend/diplom_project
ls # заходим в папку где лежит  manage.py

# создаём БД для проекта
sudo su postgres
psql
CREATE DATABASE diplom_database;
ALTER USER postgres WITH LOGIN;
ALTER USER postgres WITH PASSWORD 'pass123';
\q
exit

# создаём скрытый файл .env и заполняем его (SECRET_KEY можно сгенерировать самостоятельно)
nano .env
SECRET_KEY=example
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,79.174.91.160
DB_NAME=diplom_database
DB_USER=postgres
DB_PASSWORD=pass123
DB_HOST=localhost
DB_PORT=5432
# сохраняем файл и выходим из nano

ls --all # показать все файлы (в том числе скрытые)

# создаем virtualenv для проекта (назовём также env) и активируем его
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Посмотрим, что есть или что должно быть в requirements.txt
cat requirements.txt
	Django
	psycopg2-binary
	django-environ
	gunicorn

# применяем миграции
python manage.py migrate

# проверяем, создалась ли таблица app_file в БД
sudo su postgres
psql diplom_database
\dt
\q
exit

# создаём администратора
python manage.py createsuperuser --username=admin --email=admin@mail.ru

# ОК, если миграции прошли. Проверяем в браузере
python manage.py runserver 0.0.0.0:8000

# в браузере набираем 79.174.91.160:8000
# OK

# запускаем сервер через gunicorn
ls diplom_project/
# asgi.py __init__.py __pycache__ settings.py urls.py wsgi.py

# ликвидируем процесс на 8000 порту
fuser -k 8000/tcp
gunicorn diplom_project.wsgi -b 0.0.0.0:8000

# автоматизируем gunicorn, чтобы при запуска сервера он запускался
sudo nano /etc/systemd/system/gunicorn.service

# в редакторе добавляем разделы:
[Unit]
Description=gunicorn service
Requires=gunicorn.socket
After=network.target

[Service]
User=ilya
Group=www-data
WorkingDirectory=/home/ilya/diplom_backend/diplom_project/
ExecStart=/home/ilya/diplom_backend/diplom_project/env/bin/gunicorn \
         --access-logfile - \
         --workers=3 \
         --bind unix:/run/gunicorn.sock diplom_project.wsgi:application

[Install]
WantedBy=multi-user.target
# сохраняем и выходим

sudo nano /etc/systemd/system/gunicorn.socket
# вводим пароль. 

# В редакторе добавляем разделы:
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target

sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# проверяем статус
sudo systemctl status gunicorn 

# настраиваем nginx
sudo nano /etc/nginx/sites-available/my_project
server {
    listen 80;
    listen [::]:80;

    location / {
        root  /usr/share/nginx/html;
        index  index.html index.htm;
	try_files $uri $uri/index.html /index.html =404;
    }

    location /backend {
        rewrite ^/backend/(.*) /$1 break;
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP ip_address;
   }
}
# сохраняем и выходим

# делаем символьную ссылку на конфиг в папке с включенными сайтами
sudo ln -s /etc/nginx/sites-available/my_project /etc/nginx/sites-enabled/my_project
sudo systemctl restart nginx
sudo systemctl status nginx

# смотрим, есть ли настройки nginx по умолчанию, если да - удаляем и перезапускаем nginx
ls -l /etc/nginx/sites-enabled
sudo rm -rf  /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# настроим максимальный размер передаваемого файла - 100 мегабайт
# вписываем строчку в секцию http и сохраняем файл nginx.conf
sudo nano /etc/nginx/nginx.conf
client_max_body_size 100M;

# проверяем синтаксис конфигурационных файлов на наличие ошибок и перезагружаем его
sudo nginx -t 
sudo systemctl reload nginx

# Необходимо клонировать фронтенд на локальный ПК и прописать  адрес сервера (API_URL) по пути my-app\src\common\system-var.js 
# затем выполнить пересборку проекта с помощью команды npm run rebuild и сделать git push

# клонируем фронтенд 
git clone https://github.com/Dolinin2021/diplom_frontend.git

# устанавливаем файловый менеджер
sudo apt -y install mc

# выходим и заходим под пользователем root
exit 
ssh root@79.174.91.160

# запускаем файловый менеджер
mc

# копируем содержимое папки dist репозитория с фронтендом по пути home/ilya/diplom_backend/diplom_project/diplom_frontend/
# на адрес usr/share/nginx/html, перезаписываем файл index.html

sudo systemctl restart nginx

# теперь заходим по адресу http://79.174.91.160/
```

## Маршруты
* Добавление нового пользователя `POST useradd/`
* Список пользователей `GET userlist/`
* Информация о конкретном пользователе `GET userlist/<int:pk>/`
* Изменение параметров пользователя, а также удаление пользователя `PUT DELETE user/change/<int:pk>/`
* Список файлов текущего пользователя, а также добавление нового файла в файловое хранилище текущего пользователя `GET POST api/v1/filelist/`
* Список файлов конкретного пользователя, а также добавление нового файла в файловое хранилище конкретного пользователя `GET POST api/v1/filelist/<int:pk>/`
* Работа с текущим файлом (получение данных, генерация ссылки, обновление, удаление) `GET PUT PATCH DELETE api/v1/filelist/detail/<int:pk>/`
* Авторизация `POST api/v1/token/`
* Обновление access-токена `POST api/v1/token/refresh/`

## Библиотеки
* asgiref
* certifi
* charset-normalizer
* Django
* django-cors-headers
* djangorestframework
* djangorestframework-jwt
* djangorestframework-simplejwt
* django-environ
* gunicorn
* environ
* idna
* psycopg2-binary
* PyJWT
* pytz
* requests
* sqlparse
* typing-extensions
* tzdata
* urllib3
* wget


## Адрес проекта
[http://79.174.91.160/](http://79.174.91.160/)
