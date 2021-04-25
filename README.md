# PDF mail merger

> PDF mail merger, PDF editor, PDF generator using Excel & CSV

## Local setup

Make sure you got `npm` and `poetry` beforehand.

```
npm install
poetry install
```

Run the Django server (`poetry run ./manage.py runserver`) and Webpack in another tab (`npm run start`).

Or just: `poetry run honcho start`


## Production

Compile assets first with `npm run build`,
Then use Django collectstatic: `poetry run ./manage.py collectstatic`.

## Hosted version

[pdf.tixsumo.com](https://pdf-mail-merger.tixsumo.com).


## Self-host

Ubuntu 18.04


```
# Node
curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt install -y nodejs

# Poetry
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.9 python3.9-distutils
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

# Postgres
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install postgresql-13

# Postgres create user
# sudo -u postgres psql
# create database pdf_mail_merger;
# create user pdf_mail_merger with encrypted password 'pdf_mail_merger';
# grant all privileges on database pdf_mail_merger to pdf_mail_merger;
```
