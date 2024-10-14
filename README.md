# PostgreSQL-Browser
A PostgreSQL Browser, similar to SQLiteBrowser with far less features (for now).

![](./screenshot_cli.png)
![](./screenshot.png)

## Installation

```python
# Append --force to update
pipx install "git+https://github.com/RyanGreenup/PostgreSQL-Browser"
```

## Usage

For testing purposes, consider the attached [docker-compose.yml](./docker-compose.yml) file to spin up a PostgreSQL instance.

```bash
cd $(mktemp -d)
git clone https://github.com/RyanGreenup/PostgreSQL-Browser"
cd PostgreSQL-Browser
docker-compose up -d
docker-compose logs -f
# C-c
```

```python
pg_browser --host localhost --password postgres --username postgres --port 5432
```

## Motivation

I wanted to browse my [linkwarden](https://github.com/linkwarden/linkwarden) database, and I didn't want to use the command line, now I can simply:

```python
alias lw_db="pg_browser  --host localhost --password ${LW_DB_PASS} --username postgres --port 37194"
lw_db
```





